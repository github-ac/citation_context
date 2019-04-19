import json
import argparse
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

def args_parse():
    description = ''' Prints the n most cited titles
                  '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--index',
                        dest='index',
                        help='Name of the Elasticsearch index.',
                        type=str,
                        default='titles',
                       )
    parser.add_argument('-n', '--n',
                        dest='n',
                        help='Number of titles to fetch.',
                        type=int,
                        default=10,
                       )
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = args_parse()
    es = Elasticsearch()
    s = Search(using=es, index=args.index)[:0]
    s.aggs.bucket('group_by_state', 'terms', field='title.keyword', size=args.n)
    res = s.execute()
    for bucket in res['aggregations']['group_by_state']['buckets']:
        print(bucket['doc_count'], bucket['key'])
