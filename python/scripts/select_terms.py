#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Selects the terms from the PRF results."""

from __future__ import absolute_import, division, print_function
import argparse
from operator import neg
import re

from cc_emergency.utils import openall, itemgetter


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Selects the terms from the PRF results.')
    parser.add_argument('input_file', help='the PRF result file.')
    parser.add_argument('--query-file', '-q',
                        help='the original query file: for filtering.')
    parser.add_argument('--print', '-p', default='all',
                        choices=['new', 'query', 'missing', 'all'],
                        help='what to print when -q is specified. "new" '
                             '(the default) prints terms not in the query '
                             'file; "query" is the opposite, while "missing" '
                             'prints the terms in that query file that are '
                             'missing from the results. "all" prints '
                             'everything, with the label as an additional '
                             'column.')
    parser.add_argument('--sort-by', '-s', default='rdw',
                        help='what to sort the results by. "r" stands for '
                             'ratio, "d" for DF and "w" for the word. The '
                             'default "rdw" then sorts by ratio first, DF '
                             'second, and word form last.')
    parser.add_argument('--min-udf', type=int, help='the minimum unigram df.')
    parser.add_argument('--max-udf', type=int, help='the maximum unigram df.')
    parser.add_argument('--min-bdf', type=int, help='the minimum bigram df.')
    parser.add_argument('--max-bdf', type=int, help='the maximum bigram df.')
    parser.add_argument('--min-ur', type=float, help='the minimum unigram ratio.')
    parser.add_argument('--min-br', type=float, help='the minimum bigram ratio.')
    args = parser.parse_args()

    if not re.match('^[rdf]{1,3}$', args.sort_by):
        parser.error('Invalid --sort-by pattern: only "r", "d", and "w" are '
                     'allowed, and each at most once.')
    return args


def read_input(input_file):
    with openall(input_file) as inf:
        return [(w, float(r), *map(int, *_)) for w, r, *_ in
                (line.strip().split('\t') for line in inf)]


def sorter(pattern):
    """Creates the sorter function based on the pattern."""
    indices = [{'w': 0, 'r': 1, 'd': 3}[c] for c in pattern]
    defaults = [{'w': None, 'r': 0, 'd': 0}[c] for c in pattern]

    def key(obj):
        return tuple(v if isinstance(v, str) else neg(v)
                     for v in itemgetter(indices, defaults=defaults))
    return key


def get_thresholds(args, unigram):
    prefix = 'u' if unigram else 'b'
    return (
        getattr(args, 'min_{}r'.format(prefix)),
        getattr(args, 'min_{}df'.format(prefix)),
        getattr(args, 'max_{}df'.format(prefix))
    )


def read_queries(query_file):
    with openall(query_file) as inf:
        return set(l.strip() for l in inf.readlines())

def main():
    args = parse_arguments()
    data = read_input(args.input_file)
    if args.query_file:
        queries = read_queries(args.query_file)
    else:
        queries = None

    sorted_data = {'new': [], 'query': []}
    for item in data:
        min_r, min_df, max_df = get_thresholds(args, ' ' not in item[0])
        if min_r is not None and float(item[1]) < min_r:
            continue
        if len(item) > 2:
            if min_df is not None and int(item[-1]) < min_df:
                continue
            if max_df is not None and max_df < int(item[-1]):
                continue
        if queries and item[0] in queries:
            sorted_data['query'].append(item)
        else:
            sorted_data['new'].append(item)
    if queries:
        have_it = set(map(itemgetter(0), queries))
        sorted_data['missing'] = queries - have_it

    if args.print == 'all':
        for item in sorted(sorted_data['new'], key=sorter(args.sort_by)):
            print('\t'.join(map(str, item)) + '\tnew')
        for item in sorted(sorted_data['query'], key=sorter(args.sort_by)):
            print('\t'.join(map(str, item)) + '\tquery')
        for item in sorted(sorted_data['missing'], key=sorter(args.sort_by)):
            print(item + '\tmissing')
    else:
        for item in sorted(sorted_data[args.print], key=sorter(args.sort_by)):
            print('\t'.join(map(str, item)))

if __name__ == '__main__':
    main()
