import json
import argparse
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

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
                        default=100,
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
    body = {'query': {'constant_score': {
                        'filter': {'terms': {f'{label_in}.keyword': items_in}}
                       }
                     },
            'size': 0,
            'aggs': {'group_by_state': {
                        'terms': {'field': f'{label_out}.keyword',
                                  'size': max_buckets}
                        }
                    }
           }
    body = json.dumps(body)
    res = es.search(index=index, body=body)
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
    body = {'query': {'constant_score': {
                           'filter': {'terms': {'title.keyword': titles}}
                        }
                      },
            'size': size,
           }
    body = json.dumps(body)
    res = es.search(index=index, body=body)
    citations = [(hit['_source']['file'], hit['_source']['ref_id']) for hit in res['hits']['hits']]
    return citations

def ref_context(ref_txt, max_before):
    ''' Extract context around an xref tag within the main text of an article.
        Args: ref_txt: BeautifulSoup tag
              max_before: context length, as number of characters before xref
    '''
    context = ''
    for sib in ref_txt.previous_siblings:
        try:
            text = sib.strip()
        except:
            continue
        context = text + context
        if len(context) >= max_before:
            break
    context = context.replace('\n', '')
    if context.endswith('['):
        context = context[:-1]
    context = context[-max_before:].strip()
    return context

if __name__ == '__main__':
    args = args_parse()
    es = Elasticsearch()
    citations = get_citations(args.title, index=args.index, size=args.n)
    for filename, ref_id in citations:
        article_path = args.data_dir + filename
        with open(article_path, 'rb') as fh:
            content = fh.read().decode('utf-8')
        soup = BeautifulSoup(content, features='html.parser')

        ref_txts = soup.find_all('xref', attrs={'ref-type': 'bibr', 'rid': ref_id})
        if not ref_txts:
            continue
        for ref_txt in ref_txts:
            sentence = ref_context(ref_txt, max_before=args.context_before)
            if sentence:
                print(sentence)
