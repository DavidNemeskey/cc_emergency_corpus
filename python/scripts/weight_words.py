#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Weights words, based on the output of reduce_tf_df. Two options are available:
take the DF and compute IDF, or take the TF in two different result files and
compute the log ratio, as per the paper.
"""

from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
import json
import math

from cc_emergency.utils import openall


def parse_arguments():
    parser = ArgumentParser(
        description='Weights words, based on the output of reduce_tf_df. Two '
                    'options are available: take the DF and compute IDF, or '
                    'take the TF in two different result files and compute '
                    'the log ratio, as per the paper. The latter is triggered '
                    'by specifying a second frequency file.')
    parser.add_argument('freq_file',
                        help='the file resulting from reduce_tf_df.')
    parser.add_argument('base_freq_file', nargs='?',
                        help='base frequencies for log ratio weighting; a '
                             'file resulting from reduce_tf_df.')
    parser.add_argument('--num-docs', '-n', type=int,
                        help='the total number of documents. Only interesting '
                             'for the DF case.')
    parser.add_argument('--threshold', '-t', type=float, default=float('-inf'),
                        help='a threshold; words with weights below this are '
                             'dropped.')
    parser.add_argument('--word-filter', '-w',
                        help='a word list file to filter the words we output.')
    args = parser.parse_args()

    if args.num_docs and args.base_freq_file:
        parser.error('--num-docs is only valid when the base frequency file '
                     'is not specified.')
    if not args.num_docs and not args.base_freq_file:
        parser.error('--num-docs is required if computing DF.')
    return args


def load_file(freq_file, what='DF'):
    with openall(freq_file) as inf:
        j = json.load(inf)
    return j[what]


def compute_idfs(dfs, num_docs):
    return {word: max(math.log((num_docs - df + 0.5) / (df + 0.5)), 0)
            for word, df in dfs.items()}


def compute_tf_ratio(tfs, base_tfs, size, base_size):
    log_size_ratio = math.log(size / base_size)
    return {word: math.log(tf / base_tfs[word]) - log_size_ratio
            for word, tf in tfs.items() if base_tfs.get(word)}


class WordFilter(object):
    def __init__(self, filter_file=None):
        if filter_file:
            with openall(filter_file) as inf:
                self.words = {l.strip().split('\t', 1)[0] for l in inf}
        else:
            self.words = set()

    def __call__(self, word):
        return True if not self.words or word in self.words else False


def main():
    args = parse_arguments()
    df_mode = not bool(args.base_freq_file)
    word_filter = WordFilter(args.word_filter)
    if df_mode:
        dfs = {w: f for w, f in load_file(args.freq_file, 'DF').items()
               if word_filter(w)}
        to_print = compute_idfs(dfs, args.num_docs)
    else:
        tfs = {w: f for w, f in load_file(args.freq_file, 'TF').items()
               if word_filter(w)}
        size = sum(tfs.values())
        base_tfs = load_file(args.base_freq_file, 'TF')
        base_size = sum(base_tfs.values())
        to_print = compute_tf_ratio(tfs, base_tfs, size, base_size)
    for word, weight in sorted(to_print.items(), key=lambda kv: (-kv[1], kv[0])):
        if weight >= args.threshold:
            print('{}\t{}'.format(word, weight))


if __name__ == '__main__':
    main()
