#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Runs the variants of the emscan algorithm."""

import argparse
from functools import partial
import inspect
import logging

import networkx as nx

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
    parser.add_argument('--graph', '-g', type=str,
                        help='if specified, the "attraction graph" of the '
                             'cluster is written here.')
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
    kwargs = {k: getattr(args, k) for k in list(s.parameters)[3:-1]}
    return partial(emscan, *fn_args, **kwargs)


def main():
    args = parse_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info('Loading embedding {}...'.format(args.vector_file))
    words, vectors = read_vectors(args.vector_file, normalize=True)
    logging.info('Loading queries from {}...'.format(args.query_file))
    with open(args.query_file) as inf:
        query = set(l.strip() for l in inf)
    qwords, qindices = zip(*[(w, i) for i, w in enumerate(words)
                             if w in set(query)])
    emscan = get_emscan_params(args, words, vectors)

    if args.graph:
        G = nx.DiGraph()
        for qi in qindices:
            G.add_node(words[qi], it=0)
    else:
        G = None

    logging.info('Running EMSCAN...')
    indices = list(qindices)
    for it in range(args.iterations):
        new_indices = emscan(indices, graph=G)
        logging.info('Iteration {}: {} words.'.format(it + 1, len(new_indices)))
        if len(new_indices) == len(indices):
            logging.info('No new words found.')
            break
        if args.max_cluster and len(new_indices) >= args.max_cluster:
            logging.info('Maximum cluster size exceeded.')
            break
        indices = new_indices
    logging.info('Done.')

    for word in sorted(words[indices]):
        print(word)
    if args.graph:
        nx.write_graphml(G, args.graph + '.graphml')


if __name__ == '__main__':
    main()
