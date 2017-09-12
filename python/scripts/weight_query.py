#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Weights queries, based on the word weights file (created by weight_words.py).
This is the input to the search pipeline.
"""

from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from operator import itemgetter

from cc_emergency.utils import openall


def parse_arguments():
    parser = ArgumentParser(
        description='Weights queries, based on the word weights file (created '
                    'by weight_words.py). This is the input to the search '
                    'pipeline.')
    parser.add_argument('query_file',
                        help='a file that contains one word per line. The '
                             'output is the same list, with the word weight '
                             'appended to each line.')
    parser.add_argument('weight_file',
                        help='a weight file, the output of weight_words.py.')
    parser.add_argument('--threshold', '-t', type=float, default=float('-inf'),
                        help='a threshold; words with weights below this are '
                             'dropped.')
    return parser.parse_args()


def main():
    args = parse_arguments()
    with openall(args.weight_file) as inf:
        weights = {word: float(weight) for word, weight
                   in (line.strip().split('\t') for line in inf)}
    with openall(args.query_file) as inf:
        query = {qword: weights.get(qword) for qword in
                 map(lambda l: l.strip().split('\t')[0], inf)}
    query = sorted(filter(lambda ww: ww[1], query.items()),
                   key=itemgetter(1), reverse=True)
    for qword, qweight in query:
        if qweight >= args.threshold:
            print('{}\t{}'.format(qword, qweight))


if __name__ == '__main__':
    main()
