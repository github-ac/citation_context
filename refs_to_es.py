import os
import glob
import json
import argparse
from multiprocessing import Pool, cpu_count
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

def args_parse():
    description = '''parse xml articles and index citations from ref-list in elasticsearch.
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
    parser.add_argument('--delete_index',
                        dest='delete_index',
                        help='Delete index before parsing articles.',
                        action='store_true'
                       )
    parser.add_argument('--n_processes',
                        dest='n_processes',
                        help='Number of parallel processes',
                        type=int,
                        default=cpu_count(),
                       )
    parser.add_argument('--n_articles',
                        dest='n_articles',
                        help='Maximum number of articles to parse',
                        type=int,
                        default=10000,
                       )
    parser.add_argument('--package_size',
                        dest='package_size',
                        help='Package size for bulk indexing.',
                        type=int,
                        default=50,
                       )
    args = parser.parse_args()
    return args

def get_articles(data_dir, n):
    ''' Collect at most n articles recursively within data_dir.
        Article extensions must end with xml.
        Returns: list of article full paths
    '''
    articles = []
    articles_gen = glob.iglob(os.path.join(data_dir, '**/*xml'), recursive=True)
    for _ in tqdm(range(n)):
        try:
            articles.append(next(articles_gen))
        except StopIteration:
            break
    return articles

def package_articles(articles, size):
    ''' Split articles list in smaller packages for bulk indexing.
        A size of 500 corresponds approximately to 5MB payloads.
    '''
    return [articles[x:(x + size)] for x in range(0, len(articles), size)]

def bulk_append(data, new, index):
    ''' Add to json payload.
    '''
    data += '\n{"index": {"_index": "%s", "_type": "type"}}\n%s\n' % (index, json.dumps(new))
    return data

def file_in_index(filename, index):
    s = Search(using=es, index=index)
    s = s.query('constant_score', filter=Q('terms', **{'file.keyword': [filename]}))
    res = s.execute()
    return res.hits.total['value'] > 0

def process(package):
    ''' Function called by multiple processes.
        Receives a list of article paths and indexes all citations at once.
    '''
    args = args_parse()
    data = ''
    for article in package:
        if file_in_index(article.split(args.data_dir)[1], args.index):
            continue
        try:
            with open(article, 'rb') as fh:
                content = fh.read().decode('utf-8')
            soup = BeautifulSoup(content, features='html.parser')
            ref_list = soup.find('ref-list')
            if not ref_list:
                continue
            refs = ref_list.findChildren('ref')
            for ref in refs:
                ref_id = ref['id']
                title = ref.find('article-title')
                if not title:
                    continue
                pub_id_obj = ref.find('pub-id')
                pub_id = pub_id_obj.text if pub_id_obj else ''
                title = title.text.lower()
                ref_dict = {'ref_id': ref_id,
                            'title': title,
                            'pub_id': pub_id,
                            'file': article.split(args.data_dir)[1],
                           }
                data = bulk_append(data, ref_dict, args.index)
        except Exception as err:
            print(article, str(err))
    requests.post('http://localhost:9200/_bulk',
                  headers={'content-type': 'application/json'},
                  data=data,
                 )

if __name__ == '__main__':
    args = args_parse()
    es = Elasticsearch(maxsize=args.n_processes)

    if args.delete_index:
        requests.delete(f'http://localhost:9200/{args.index}')

    articles = get_articles(args.data_dir, args.n_articles)
    packages = package_articles(articles, size=args.package_size)

    with Pool(processes=args.n_processes) as p:
        for _ in tqdm(enumerate(p.imap_unordered(process, packages)), total=len(packages)):
            pass
