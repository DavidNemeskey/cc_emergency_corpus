#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Displays the BEV embedding in 2D."""

from __future__ import absolute_import, division, print_function
import argparse
from collections import defaultdict

import matplotlib.pyplot as plt

from cc_emergency.utils import setup_stream_logger
from cc_emergency.utils.vector_io import read_vectors, write_vectors
from cc_emergency.utils.vectors import compute_mds


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Displays the BEV in 2D. Uses metric multidimensional '
                    'scaling with angular distance to map the points to '
                    'two dimensions.')
    parser.add_argument('vector_file', help='the word vector file.')
    parser.add_argument('--bev', '-b', action='append', default=[],
                        help='the BEV list file(s) (one word per line). If not '
                             'specified, the whole vector_file is displayed, '
                             'which might be too much for the machine. It is '
                             'possible to specify more than one file, in '
                             'which case all sets are displayed with different '
                             'colors.')
    parser.add_argument('--write-vectors', '-w',
                        help='if specified, writes the vectors filtered by '
                             'all the BEVs back to this file.')
    parser.add_argument('--distance', '-d', choices=['cos', 'euc'],
                        help='the distance metric to use: cosine similarity '
                             'or Euclidean distance.')
    parser.add_argument('--log-level', '-L', type=str, default=None,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    if len(args.bev) > 3:
        parser.error('At most three word lists are accepted.')
    return args


def vector_stuff(vector_file, bev_files, write_file):
    colors = {1: 'r', 2: 'g', 4: 'b', 3: 'y', 5: 'm', 6: 'c', 7: 'k'}
    points = defaultdict(int)
    if bev_files:
        for i, bev_file in enumerate(bev_files):
            with open(bev_file) as inf:
                for word in set(inf.read().strip().split('\n')):
                    points[word] |= pow(2, i)
        points = {w: colors[c] for w, c in points.items()}
    words, vectors = read_vectors(vector_file, keep_words=points.keys())
    if write_file:
        write_vectors(words, vectors, write_file)
    if not points:
        points = {w: 'r' for w in words}
    return words, vectors, points


def main():
    args = parse_arguments()
    setup_stream_logger(args.log_level, 'cc_emergency')
    words, vectors, points = vector_stuff(
        args.vector_file, args.bev, args.write_vectors)
    coords = compute_mds(vectors, args.distance)

    # Plotting -- ungh...
    x_min = coords[:, 0].min()
    x_max = coords[:, 0].max()
    y_min = coords[:, 1].min()
    y_max = coords[:, 1].max()

    plt.plot(coords[:, 0], coords[:, 1], 'bx')
    plt.axis([x_min - 0.1, x_max + 0.1, y_min - 0.1, y_max + 0.1])
    plt.show()


if __name__ == '__main__':
    main()
