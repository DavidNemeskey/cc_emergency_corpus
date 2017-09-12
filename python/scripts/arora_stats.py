#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Analysis of an emergency list based on an Arora embedding."""

from __future__ import absolute_import, division, print_function
import argparse
from collections import Counter, defaultdict, OrderedDict
from functools import reduce
from operator import itemgetter

from cc_emergency.utils import openall, setup_stream_logger
from cc_emergency.utils.vector_io import read_vectors


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Analysis of an emergency list based on an Arora embedding.')
    parser.add_argument('vector_file', help='the (sparse) word vector file.')
    parser.add_argument('--bev', '-b', action='append', default=[],
                        help='the BEV list file(s) (one word per line).')
    parser.add_argument('--values', '-v', action='store_true',
                        help='also print the topic coordinate values for each '
                             'word.')
    parser.add_argument('--filter-unique', '-f', action='store_true',
                        help='do not print topics that only encompass a '
                             'single word.')
    parser.add_argument('--log-level', '-L', type=str, default=None,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    if len(args.bev) > 3:
        parser.error('At most three word lists are accepted.')
    return args


def read_bev(bev_file):
    with openall(bev_file) as inf:
        return set([line.strip() for line in inf])


def word_list_repr(word_list, print_values):
    if print_values:
        return ', '.join('{} [{:.2f}]'.format(w, c) for w, c
                         in sorted(word_list.items(), key=itemgetter(1),
                                   reverse=True))
    else:
        return ', '.join(sorted(word_list.keys()))


def main():
    args = parse_arguments()
    setup_stream_logger(args.log_level, 'cc_emergency')
    bevs = OrderedDict([(bev_file, read_bev(bev_file)) for bev_file in args.bev])
    keep_words = reduce(lambda alls, s: alls.union(s), bevs.values())
    words, vectors = read_vectors(args.vector_file, normalize=True,
                                  keep_words=keep_words)
    swords = set(words)

    for bev_file, bev in bevs.items():
        bev_counter = Counter()
        topic_words = defaultdict(dict)
        not_found = []
        for word in bev:
            if word in swords:
                row = words.index(word)
                for topic in vectors[row].nonzero()[1]:
                    topic_words[topic][word] = vectors[row, topic]
                    bev_counter[topic] += 1
            else:
                not_found.append(word)

        if args.filter_unique:
            to_delete = [t for t, cnt in bev_counter.items() if cnt == 1]
            for topic in to_delete:
                del bev_counter[topic]
                del topic_words[topic]

        print('BEV file: {}'.format(bev_file))
        if not_found:
            print('Words not found in the embedding: {}'.format(
                ', '.join(not_found)))
        print('Topic frequencies:\n  {}'.format(
            '\n  '.join('{}: {}'.format(*p) for p in bev_counter.most_common())))
        print('\nWords per topic:\n  {}'.format(
            '\n  '.join('{}: {}'.format(t, word_list_repr(ws, args.values))
                        for t, ws in sorted(topic_words.items(),
                                            key=lambda tws: -len(tws[1])))))
        print('\n')


if __name__ == '__main__':
    main()
