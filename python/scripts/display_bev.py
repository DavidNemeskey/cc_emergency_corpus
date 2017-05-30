#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Displays the BEV embedding in 2D."""

from __future__ import absolute_import, division, print_function
import argparse

from cc_emergency.utils.vectors import read_vectors, write_vectors


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Displays the BEV in 2D.')
    parser.add_argument('vector_file', help='the word vector file.')
    parser.add_argument('--bev', '-b',
                        help='the BEV list file (one word per line). If not '
                             'specified, the whole vector_file is displayed, '
                             'which might be too much for the machine.')
    parser.add_argument('--write-vectors', '-w',
                        help='if specified, writes the vectors filtered by '
                             'the BEV back to this file.')
    parser.add_argument('--distance', '-d', choices=['cos', 'euc'],
                        help='the distance metric to use: cosine similarity '
                             'or Euclidean distance.')
    parser.add_argument('--log-level', '-L', type=str, default=None,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    return args


def vector_stuff(vector_file, bev_file, write_vectors):
    if bev_file:
        with open(bev_file) as inf:
            bev = set(inf.read().split('\n'))
    else:
        bev = None
    words, vectors = read_vectors(vector_file, bev)
    if write_vectors:
        write_vectors(words, vectors, write_vectors)
    return words, vectors


def main():
    args = parse_arguments()
    words, vectors = vector_stuff(args.vector_file, args.bev, args.write_vectors)


if __name__ == '__main__':
    main()
