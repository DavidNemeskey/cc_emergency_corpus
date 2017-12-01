#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Filters the TF / DF counts."""

from __future__ import absolute_import, division, print_function
import argparse
import json

from cc_emergency.utils import openall
from cc_emergency.functional.transform.bigrams import BigramFilter2


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Filters the TF / DF counts.')
    parser.add_argument('--field', '-f', dest='fields', required=True,
                        action='append', default=[],
                        help='Name of the (base) field. The associated bigram '
                             'field must be called <field>_bigrams.')
    parser.add_argument('--unigram', '-u', type=int,
                        help='the minimum unigram document frequency.')
    parser.add_argument('--bigram', '-b', type=int,
                        help='the minimum bigram document frequency.')
    parser.add_argument('--cross-filter', '-c', action='store_true',
                        help='if present, bigrams whose unigrams were filtered '
                             'are also removed.')
    parser.add_argument('input_file',
                        help='the input file. The result of running the '
                             'reduce_tf_df job.')
    parser.add_argument('output_file',
                        help='the filtered output file.')
    args = parser.parse_args()

    if not args.unigram and not args.bigram:
        parser.error('At least one of -u and -b must be specified.')
    if args.cross_filter and not args.unigram:
        parser.error('-c is only valid if -u is specified.')
    return args


def filter_dicts(dfs, tfs, min_df):
    """Filters the dictionaries based on the minimum DF specified."""
    dfs_f = {k: v for k, v in dfs.items() if v >= min_df}
    tfs_f = {k: v for k, v in tfs.items() if k in dfs_f}
    return dfs_f, tfs_f


def cross_filter(uni_dfs, bi_dfs, bi_tfs):
    """Filters bigrams whose parts are not in the unigram dictionaries."""
    unis = set(uni_dfs.keys())
    bi_dfs_f = {k: v for k, v in bi_dfs.items()
                if BigramFilter2.has_valid_split(k, unis)}
    bi_tfs_f = {k: v for k, v in bi_tfs.items() if k in bi_dfs_f}
    return bi_dfs_f, bi_tfs_f


def main():
    args = parse_arguments()
    with openall(args.input_file) as inf:
        j = json.load(inf)
    for field in args.fields:
        uni_dfs = j[field]['DF']
        bi_dfs = j[field + '_bigrams']['DF']
        uni_tfs = j[field]['TF']
        bi_tfs = j[field + '_bigrams']['TF']
        print('{} field statistics'.format(field))
        print('  Unigrams: {}'.format(len(uni_dfs)))
        print('  Bigrams: {}'.format(len(bi_dfs)))
        print('  Unigram tokens: {}'.format(sum(uni_tfs.values())))
        print('  Bigram tokens: {}'.format(sum(bi_tfs.values())))
        print('{} after filtering'.format(field, args.unigram))
        if args.unigram:
            uni_dfs, uni_tfs = filter_dicts(uni_dfs, uni_tfs, args.unigram)
            print('  Filtered unigrams ({}): {}'.format(
                args.unigram, len(uni_dfs)))
            print('  Filtered unigram tokens ({}): {}'.format(
                args.unigram, sum(uni_tfs.values())))
            if args.cross_filter:
                bi_dfs, bi_tfs = cross_filter(uni_dfs, bi_dfs, bi_tfs)
                print('  Cross-filtered bigrams: {}'.format(
                    args.bigram, len(bi_dfs)))
                print('  Cross-filtered bigram tokens: {}'.format(
                    args.bigram, sum(bi_tfs.values())))
        if args.bigram:
            bi_dfs, bi_tfs = filter_dicts(bi_dfs, bi_tfs, args.bigram)
            print('  Filtered bigrams ({}): {}'.format(
                args.bigram, len(bi_dfs)))
            print('  Filtered bigram tokens ({}): {}'.format(
                args.bigram, sum(bi_tfs.values())))


if __name__ == '__main__':
    main()
