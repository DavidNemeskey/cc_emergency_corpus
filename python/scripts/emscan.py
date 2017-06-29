#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Runs the variants of the emscan algorithm."""

import argparse
from functools import partial
import inspect
import logging

from cc_emergency.utils.vector_io import read_vectors
from cc_emergency.utils.vectors import emscan_first, emscan_dcg  # noqa


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Runs the variants of the emscan algorithm.')
    parser.add_argument('vector_file', help='the word vector file.')
    parser.add_argument('query_file', help='the query file, one word per line.')
    parser.add_argument('--min-similarity', '-s', type=float, default=0.5,
                        help='the minimum similarity with a cluster node to '
                             'add a vertex to the candidates [0.5].')
    parser.add_argument('--max-cluster', '-c', type=int, default=None,
                        help='the maximum cluster size: the stopping criterion.')
    parser.add_argument('--iterations', '-i', type=int, default=10,
                        help='the maximum number of iterations [10].')
    parser.add_argument('--log-level', '-L', type=str, default='critical',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level [critical].')
    subparsers = parser.add_subparsers(
        dest='emscan', description='', help='choose the EMSCAN variant.')
    subparsers.add_parser('first', description='EMSCAN_first')
    dcg_p = subparsers.add_parser('dcg', description='EMSCAN_dcg')
    dcg_p.add_argument('--dcg-length', '-l', type=int, default=5,
                       help='the number of top results to compute the DCG '
                            'from [5].')
    dcg_p.add_argument('--min-dcg', '-m', type=float, default=1,
                       help='the DCG threshold to add a candidate to the '
                            'cluster [1].')

    args = parser.parse_args()
    if not args.emscan:
        parser.error('No subcommand specified.')
    return args


def get_emscan_params(args, *fn_args):
    emscan = globals()['emscan_' + args.emscan]
    s = inspect.signature(emscan)
    ba = s.bind_partial(*fn_args)
    for k in s.parameters.keys():
        if k not in ba.arguments:
            ba.arguments[k] = getattr(args, k)
    return partial(emscan, **ba.arguments)


def main():
    args = parse_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')

    words, vectors = read_vectors(args.vector_file, normalize=True)
    with open(args.query_file) as inf:
        query = [l.strip() for l in inf]
    qindices = {w: i for i, w in enumerate(words) if w in set(query)}
    emscan = get_emscan_params(args, words, vectors)

    indices = qindices
    for it in range(args.iterations):
        indices = emscan(indices)
        logging.info('Iteration {}: {} words.'.format(it + 1, len(indices)))
        if args.max_cluster and len(indices) >= args.max_cluster:
            break
    for word in sorted(words[indices]):
        print(word)


if __name__ == '__main__':
    main()
