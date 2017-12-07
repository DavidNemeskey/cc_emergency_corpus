#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Selects the terms from the PRF results."""

from __future__ import absolute_import, division, print_function
import argparse

from cc_emergency.utils import openall


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Selects the terms from the PRF results.')
    parser.add_argument('input_file', help='the PRF result file.')
    parser.add_argument('--min-udf', type=int, help='the minimum unigram df.')
    parser.add_argument('--max-udf', type=int, help='the maximum unigram df.')
    parser.add_argument('--min-bdf', type=int, help='the minimum bigram df.')
    parser.add_argument('--max-bdf', type=int, help='the maximum bigram df.')
    parser.add_argument('--min-ur', type=float, help='the minimum unigram ratio.')
    parser.add_argument('--min-br', type=float, help='the minimum bigram ratio.')
    return parser.parse_args()


def read_input(input_file):
    with openall(input_file) as inf:
        return [line.strip().split('\t') for line in inf]


def get_thresholds(args, unigram):
    prefix = 'u' if unigram else 'b'
    return (
        getattr(args, 'min_{}r'.format(prefix)),
        getattr(args, 'min_{}df'.format(prefix)),
        getattr(args, 'max_{}df'.format(prefix))
    )

def main():
    args = parse_arguments()
    data = read_input(args.input_file)
    for item in data:
        min_r, min_df, max_df = get_thresholds(args, ' ' in item[0])
        if min_r and item[1] < min_r:
            continue
        if len(item) > 2:
            if min_df and item[-1] < min_df:
                continue
            if max_df and max_df < item[-1]:
                continue
        print('\t'.join(map(str, item)))


if __name__ == '__main__':
    main()
