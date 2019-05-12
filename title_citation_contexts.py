import json
import re
import argparse
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import spacy

def args_parse():
    description = ''' Finds all title/pub_id variants for a given title,
                      then prints all citation contexts.
                  '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--data_dir',
                        dest='data_dir',
                        help='Data directory. We recursively find xml files in it.',
                        type=str,
                        default='data',
                       )
    parser.add_argument('--index',
                        dest='index',
                        help='Name of the Elasticsearch index.',
                        type=str,
                        default='titles',
                       )
    parser.add_argument('--title',
                        dest='title',
                        help='Title to search.',
                        type=str,
                        required=True,
                       )
    parser.add_argument('-n', '--n',
                        dest='n',
                        help='Max number of contexts to fetch.',
                        type=int,
                        default=10,
                       )
    parser.add_argument('--context_before',
                        dest='context_before',
                        help='Number of context characters before citation.',
                        type=int,
                        default=500,
                       )
    parser.add_argument('--context_after',
                        dest='context_after',
                        help='Number of context characters after citation.',
                        type=int,
                        default=500,
                       )
    args = parser.parse_args()
    return args

def get_items(items_in, label_in, label_out, index, max_buckets=1000):
    ''' Returns all pub_ids for a given title, or all titles for a pub_id
        Args: items_in: str or list
              label_in: title or pub_id. Field of items_in
              label_out: title or pub_id. Output field
              max_buckets: max number of outputs.
        Returns: list
    '''
    if not isinstance(items_in, list):
        items_in = [items_in]
    s = Search(using=es, index=index)[:0]
    s = s.query('constant_score', filter=Q('terms', **{f'{label_in}.keyword': items_in}))
    s.aggs.bucket('group_by_state', 'terms', field=f'{label_out}.keyword', size=max_buckets)
    res = s.execute()
    buckets = res['aggregations']['group_by_state']['buckets']
    items_out = [b['key'] for b in buckets if b['key']]
    return items_out

def get_titles(items_in, index, max_buckets=1000):
    ''' Returns all titles for a given list of pub_ids
    '''
    return get_items(items_in,
                     label_in='pub_id',
                     label_out='title',
                     index=index,
                     max_buckets=max_buckets,
                    )

def get_pub_ids(items_in, index, max_buckets=1000):
    ''' Returns all pub_ids for a given list of titles
    '''
    return get_items(items_in,
                     label_in='title',
                     label_out='pub_id',
                     index=index,
                     max_buckets=max_buckets,
                    )

def recurse_titles(titles_in, index):
    ''' Given a list of titles, find all corresponding pub_ids.
        Then for all such pub_ids find all titles.
        Continue recursively until no more titles are added.
    '''
    titles = set(titles_in)
    pub_ids = get_pub_ids(list(titles_in), index)
    pub_ids = [p for p in pub_ids if '/' in p] # discard unreliable numeric id's
    titles.update(get_titles(pub_ids, index))
    if len(titles) == len(titles_in):
        return list(titles)
    else:
        return recurse_titles(titles, index)

def get_citations(title, index, size=10):
    ''' Given a title, find all citations as (citing article file, ref_id)
    '''
    titles = recurse_titles([title], index)
    s = Search(using=es, index=index)[:size]
    s = s.query('constant_score', filter=Q('terms', **{'title.keyword': titles}))
    res = s.execute()
    citations = [(hit['_source']['file'], hit['_source']['ref_id']) for hit in res['hits']['hits']]
    return citations

def remove_brackets(text):
    ''' Remove round or square brackets and their content.
        See https://stackoverflow.com/a/14599280 for original regex
    '''
    re_complete = '[\(\[].*?[\)\]]' # complete bracket pairs
    re_close = '[\(\[].*' # leftover close bracket
    re_open = '.*[\)\]]' # leftover open bracket
    text = re.sub(re_complete, '', text)
    text = re.sub(re_close, '', text)
    text = re.sub(re_open, '', text)
    return text

def remove_formatting(text):
    tags = ['i', 'italic', 'b', 'bold', 'u', 'underline', 'sc',
            'emphasis', 'sub', 'sup',
           ]
    for tag in tags:
        text = text.replace(f'<{tag}>', '')
        text = text.replace(f'</{tag}>', '')
    return text

def extract_words(text):
    ''' Only return a subset of characters
    '''
    words = re.findall(r'[A-Za-z0-9.,]+', text)
    return ' '.join(words)

def siblings_context(siblings, context_len):
    ''' Collect clean sibling texts
        Args: siblings: list of BeautifulSoup siblings
              context_len: max number of characters to return
        Returns: list of strings
    '''
    sibling_texts = []
    for sib in siblings:
        try:
            text = sib.strip()
        except: # fails if it's a tag
            continue
        text = remove_brackets(text)
        text = extract_words(text)
        if text:
            sibling_texts.append(text)
        if len(' '.join(sibling_texts)) >= context_len:
            break
    return sibling_texts

def prev_context(ref_txt, context_len):
    ''' Extracts clean text before a reference
    '''
    prev_texts = siblings_context(ref_txt.previous_siblings, context_len)
    prev_text = ' '.join(prev_texts[::-1]).strip()
    prev_text = prev_text[-context_len:]
    return prev_text

def next_context(ref_txt, context_len):
    ''' Extracts clean text after a reference
    '''
    next_texts = siblings_context(ref_txt.next_siblings, context_len)
    next_text = ' '.join(next_texts).strip()
    next_text = next_text[:context_len]
    return next_text

def ref_context(ref_txt, max_before, max_after, nlp):
    ''' Extract context around an xref tag within the main text of an article.
        Args: ref_txt: BeautifulSoup tag
              max_before: context length, as number of characters before xref
              max_after: context length, as number of characters after xref
    '''
    context_before = prev_context(ref_txt, max_before)
    doc = nlp(context_before)
    before = ''
    for before in doc.sents:
        pass

    context_after = next_context(ref_txt, max_after)
    doc = nlp(context_after)
    try:
        after = next(doc.sents)
    except StopIteration:
        after = ''
    context = f'{before}<XREF>{after}'
    return context

if __name__ == '__main__':
    args = args_parse()
    es = Elasticsearch()
    nlp = spacy.load('en_core_web_sm')
    citations = get_citations(args.title, index=args.index, size=args.n)
    for filename, ref_id in citations:
        article_path = args.data_dir + filename
        with open(article_path, 'rb') as fh:
            content = fh.read().decode('utf-8')
        content = remove_formatting(content)
        soup = BeautifulSoup(content, features='html.parser')
        ref_txts = soup.find_all('xref', attrs={'ref-type': 'bibr', 'rid': ref_id})
        if not ref_txts:
            continue
        for ref_txt in ref_txts:
            context = ref_context(ref_txt, args.context_before, args.context_after, nlp)
            if context:
                print(context)
