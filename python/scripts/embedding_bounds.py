#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Computes the bounding sphere around sets of points."""

import argparse
from collections import OrderedDict
from itertools import chain
import logging

import miniball
import numpy as np

from cc_emergency.utils.vector_io import read_vectors
from cc_emergency.utils.vectors import angular_distance


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Computes the bounding sphere around sets of points.')
    parser.add_argument('vector_file', help='the word vector file.')
    parser.add_argument('--bev', '-b', action='append', default=[],
                        help='the BEV list file(s) (one word per line). If not '
                             'specified, the whole vector_file is displayed, '
                             'which might be too much for the machine. It is '
                             'possible to specify more than one file, in '
                             'which case all sets are displayed with different '
                             'colors.')
    parser.add_argument('--log-level', '-L', type=str, default='critical',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    return args


def read_stuff(vector_file, bev_files, normalize):
    sets = OrderedDict()
    if bev_files:
        for bev_file in bev_files:
            with open(bev_file) as inf:
                sets[bev_file] = set(inf.read().strip().split('\n'))
    words, vectors = read_vectors(
        vector_file, normalize, keep_words=set(chain(*sets.values())))
    return words, vectors, sets


def centroid_distribution(vectors):
    """
    Momentums of a cluster based on the distances of its points from the
    centriod.
    """
    centroid = vectors.mean(axis=0)
    centroid /= np.linalg.norm(centroid)
    dists = np.squeeze(angular_distance(centroid[np.newaxis, :], vectors))
    dists_mean = dists.mean()
    dists_std = dists.std()
    return OrderedDict([
        ('centroid', centroid),
        ('max', dists.max()),
        ('mean', dists_mean),
        ('std', dists_std),
        ('pinstd', np.sum(np.logical_and(dists_mean - dists_std < dists,
                                         dists < dists_mean + dists_std)) / len(dists))
    ])


def bounding_sphere(vectors):
    """Computes the bounding sphere of the vectors."""
    mb = miniball.Miniball(vectors)
    mb_center = mb.center()
    dists = np.squeeze(angular_distance(np.array(mb_center)[np.newaxis, :], vectors))
    dists_mean = dists.mean()
    dists_std = dists.std()
    return OrderedDict([
        ('center', mb_center),
        ('radius', np.sqrt(mb.squared_radius())),
        ('bs_max', dists.max()),
        ('bs_mean', dists_mean),
        ('bs_std', dists_std),
        ('bs_pinstd', np.sum(np.logical_and(dists_mean - dists_std < dists,
                                            dists < dists_mean + dists_std)) / len(dists))
    ])


def main():
    args = parse_arguments()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')

    words, vectors, sets = read_stuff(args.vector_file, args.bev, True)
    vectors = np.asarray(vectors)  # Miniball doesn't work on matrices
    set_indices = OrderedDict((s, []) for s in sets.keys())

    for i, word in enumerate(words):
        for s, swords in sets.items():
            if word in swords:
                set_indices[s].append(i)

    for s, indices in set_indices.items():
        v = vectors[indices]
        logging.debug('Computing centroid stats for set {}'.format(s))
        stats = centroid_distribution(v)
        logging.debug('Done computing centroid stats for set {}'.format(s))
        # logging.debug('Computing bounding sphere for set {}'.format(s))
        # bstats = bounding_sphere(v)
        # logging.debug('Computed bounding sphere for set {}'.format(s))
        centroid = stats.pop('centroid')
        # center = bstats.pop('center')
        # stats.update(bstats)
        # stats['cdist'] = angular_distance(
        #     np.array([centroid, center / np.linalg.norm(center)]))[0, 1]
        print('Stats for {}:\n  {}'.format(
            s, '\n  '.join(': '.join(map(str, kv)) for kv in stats.items())))


if __name__ == '__main__':
    main()
