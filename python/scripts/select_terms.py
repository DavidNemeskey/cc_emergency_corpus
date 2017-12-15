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
                             'prints terms not in the query '
                             'file; "query" is the opposite, while "missing" '
                             'prints the terms in that query file that are '
                             'missing from the results. The default, "all" '
                             'prints everything, with the label as an '
                             'additional column.')
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
    parser.add_argument('--min-eudf', type=int,
                        help='the minimum unigram df in the emergency subset.')
    parser.add_argument('--max-eudf', type=int,
                        help='the maximum unigram df in the emergency subset.')
    parser.add_argument('--min-ebdf', type=int,
                        help='the minimum bigram df in the emergency subset.')
    parser.add_argument('--max-ebdf', type=int,
                        help='the maximum bigram df in the emergency subset.')
    parser.add_argument('--min-udfr', type=int,
                        help='the minimum unigram df ratio.')
    parser.add_argument('--max-udfr', type=int,
                        help='the maximum unigram df ratio.')
    parser.add_argument('--min-bdfr', type=int,
                        help='the minimum bigram df ratio.')
    parser.add_argument('--max-bdfr', type=int,
                        help='the maximum bigram df ratio.')
    parser.add_argument('--all', '-a', action='store_true',
                        help='do NOT filter NNPs, numbers, tags, etc.')
    args = parser.parse_args()

    if not re.match('^[rdw]{1,3}$', args.sort_by):
        parser.error('Invalid --sort-by pattern: only "r", "d", and "w" are '
                     'allowed, and each at most once.')
    if args.print not in ['all', 'new'] and not args.query_file:
        parser.error('-p cannot be set if -q isn\'t.')
    return args


def read_input(input_file):
    with openall(input_file) as inf:
        return [(w, float(r), *map(int, _)) for w, r, *_ in
                (line.strip().split('\t') for line in inf)]


def sorter(pattern):
    """Creates the sorter function based on the pattern."""
    indices = [{'w': 0, 'r': 1, 'd': 3}[c] for c in pattern]
    defaults = [{'w': None, 'r': 0, 'd': 0}[c] for c in pattern]

    ig = itemgetter(*indices, defaults=defaults)

    def key(obj):
        return tuple(v if isinstance(v, str) else neg(v)
                     for v in ig(obj))
    return key


def get_thresholds(args, unigram):
    prefix = 'u' if unigram else 'b'
    return (
        getattr(args, 'min_{}r'.format(prefix)),
        getattr(args, 'min_{}df'.format(prefix)),
        getattr(args, 'max_{}df'.format(prefix)),
        getattr(args, 'min_e{}df'.format(prefix)),
        getattr(args, 'max_e{}df'.format(prefix)),
        getattr(args, 'min_{}dfr'.format(prefix)),
        getattr(args, 'max_{}dfr'.format(prefix)),
    )


def read_queries(query_file):
    with openall(query_file) as inf:
        return set(l.strip() for l in inf.readlines())


def filter_item(item):
    return all(filter_token(w) for w in item[0].split())


def filter_token(word):
    if all(c.isalpha() or c in ['.', '-'] for c in word):
        if word.startswith('-') or word.endswith('-'):
            return False
        if word == 'NNP':
            return False
        return True
    else:
        return False


def main():
    TOKEN, SCORE, EDF, DF = range(4)
    args = parse_arguments()
    data = read_input(args.input_file)
    if args.query_file:
        queries = read_queries(args.query_file)
    else:
        queries = None

    sorted_data = {'new': [], 'query': []}
    for item in data:
        if not args.all and not filter_item(item):
            continue
        min_r, min_df, max_df, min_edf, max_edf, min_dfr, max_dfr = get_thresholds(
            args, ' ' not in item[TOKEN])
        if min_r is not None and float(item[SCORE]) < min_r:
            continue
        if len(item) > 2:
            if min_df is not None and item[DF] < min_df:
                continue
            if max_df is not None and max_df < item[DF]:
                continue
            if min_edf is not None and item[EDF] < min_edf:
                continue
            if max_edf is not None and max_edf < item[EDF]:
                continue
            if min_dfr is not None and float(item[DF]) / item[EDF] < min_dfr:
                continue
            if max_dfr is not None and max_dfr < float(item[DF]) / item[EDF]:
                continue
        if queries and item[TOKEN] in queries:
            sorted_data['query'].append(item)
        else:
            sorted_data['new'].append(item)
    if queries:
        have_it = set(map(itemgetter(TOKEN), sorted_data['query']))
        sorted_data['missing'] = queries - have_it

    if queries:
        if args.print == 'all':
            for item in sorted(sorted_data['new'], key=sorter(args.sort_by)):
                print('\t'.join(map(str, item)) + '\tnew')
            for item in sorted(sorted_data['query'], key=sorter(args.sort_by)):
                print('\t'.join(map(str, item)) + '\tquery')
            for item in sorted(sorted_data['missing']):
                print(item + '\tmissing')
        elif args.print == 'missing':
            for item in sorted(sorted_data['missing']):
                print(item)
        else:
            for item in sorted(sorted_data[args.print], key=sorter(args.sort_by)):
                print('\t'.join(map(str, item)))
    else:
        for item in sorted(sorted_data['new'], key=sorter(args.sort_by)):
            print('\t'.join(map(str, item)))

if __name__ == '__main__':
    main()
