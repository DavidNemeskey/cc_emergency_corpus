#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Displays the BEV embedding in 2D."""

from __future__ import absolute_import, division, print_function
import argparse
from collections import defaultdict
from functools import partial

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
                             'all the BEVs back to this file. In this case, '
                             'the projection is not computed, and the script '
                             'exists right away.')
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


def vector_stuff(vector_file, bev_files, normalize):
    points = defaultdict(int)
    if bev_files:
        for i, bev_file in enumerate(bev_files):
            with open(bev_file) as inf:
                for word in set(inf.read().strip().split('\n')):
                    points[word] |= pow(2, i)
        points = {w: style for w, style in points.items()}
    words, vectors = read_vectors(
        vector_file, normalize, keep_words=points.keys())
    return words, vectors, points


def onpick(event, artist_indices, words):
    for i in event.ind:
        print(words[artist_indices[event.artist][i]])
    # print(event, event.ind, event.name, event.mouseevent,
    #       event.guiEvent, event.artist)


def main():
    args = parse_arguments()
    setup_stream_logger(args.log_level, 'cc_emergency')
    words, vectors, points = vector_stuff(
        args.vector_file, args.bev, True if args.distance == 'cos' else False)
    if args.write_vectors:
        write_vectors(words, vectors, args.write_vectors)
    else:
        styles = {
            1: {'c': '#006DDB', 'marker': '+', 'ls': '', 'mew': 2},  # blue
            2: {'c': '#920000', 'marker': 'x', 'ls': '', 'mew': 3},  # red
            4: {'c': '#FFFF6D', 'marker': '^', 'ls': ''},  # yellow
            3: {'c': '#490092', 'marker': '*', 'ls': ''},  # purple
            5: {'c': '#DBD100', 'marker': 's', 'ls': ''},  # orange
            6: {'c': '#24FF24', 'marker': 'p', 'ls': ''},  # green
            7: {'c': 'k', 'marker': 'h', 'ls': ''}  # black
        }

        coords = compute_mds(vectors, args.distance)

        # Plotting -- ungh...
        x_min = coords[:, 0].min()
        x_max = coords[:, 0].max()
        y_min = coords[:, 1].min()
        y_max = coords[:, 1].max()

        fig = plt.figure()
        ax = fig.add_subplot(111)
        artist_indices = {}
        if points:
            per_color_indices = defaultdict(list)
            for i, word in enumerate(words):
                style = points[word]
                per_color_indices[style].append(i)
            for style, indices in sorted(per_color_indices.items()):
                print(style)
                ccoords = coords[indices]
                art = ax.plot(ccoords[:, 0], ccoords[:, 1], picker=3,
                              **styles[style])[0]
                artist_indices[art] = indices
        else:
            ax.plot(coords[:, 0], coords[:, 1], 'rx', picker=3)
            artist_indices[art] = list(range(coords.shape[0]))
        ax.set_xlim(x_min - 0.1, x_max + 0.1)
        ax.set_ylim(y_min - 0.1, y_max + 0.1)
        op = partial(onpick, artist_indices=artist_indices, words=words)
        fig.canvas.mpl_connect('pick_event', op)
        # plt.show()
        plt.savefig('bev_vs_bv.eps', bbox_inches='tight', transparent=True, pad_inches=0)
        plt.savefig('bev_vs_bv.svg', bbox_inches='tight', transparent=True, pad_inches=0)


if __name__ == '__main__':
    main()
