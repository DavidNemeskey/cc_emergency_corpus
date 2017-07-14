#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Computes the bounding sphere around sets of points."""

import argparse
from collections import Counter, OrderedDict
from itertools import chain, combinations
import logging
import os

# import miniball
import numpy as np
import pandas as pd

from cc_emergency.utils.vector_io import read_vectors
from cc_emergency.utils.vectors import angular_distance


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Computes the bounding sphere around sets of points.')
    parser.add_argument('vector_file', help='the word vector file.')
    parser.add_argument('--bev', '-b', action='append', default=[],
                        help='the BEV list file(s) (one word per line).')
    parser.add_argument('--subsets', '-s', action='store_true',
                        help='also compute the statistics for the various '
                             'combinations and subsets of the specified '
                             'lists: intersections and items unique to a set.')
    parser.add_argument('--write-real', '-w', action='append', default=[],
                        help='Write the points that "really belong" to these '
                        'sets (i.e. they are in the diagonals of the confusion '
                        'matrix) to file.')
    parser.add_argument('--log-level', '-L', type=str, default='critical',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    if len(args.bev) == 0:
        parser.error('At least one list file should be specified.')
    if args.subsets and len(args.bev) == 1:
        parser.error('--subsets doesn\'t make sense if there is only one list.')
    return args


def filename_to_set(file_name):
    """Converts the file name to a set name."""
    name = os.path.basename(file_name)
    n, _, ext = name.rpartition('.')
    return n if len(ext) == 3 else name


def read_stuff(vector_file, bev_files, normalize):
    sets = OrderedDict()
    if bev_files:
        for bev_file in bev_files:
            with open(bev_file) as inf:
                sets[filename_to_set(bev_file)] = set(inf.read().strip().split('\n'))
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
        ('p_in_std', 100 * np.sum(
            np.logical_and(dists_mean - dists_std < dists,
                           dists < dists_mean + dists_std)) / len(dists)),
        ('num_words', len(dists))
    ])


# def bounding_sphere(vectors):
#     """Computes the bounding sphere of the vectors."""
#     mb = miniball.Miniball(vectors)
#     mb_center = mb.center()
#     dists = np.squeeze(angular_distance(np.array(mb_center)[np.newaxis, :], vectors))
#     dists_mean = dists.mean()
#     dists_std = dists.std()
#     return OrderedDict([
#         ('center', mb_center),
#         ('radius', np.sqrt(mb.squared_radius())),
#         ('bs_max', dists.max()),
#         ('bs_mean', dists_mean),
#         ('bs_std', dists_std),
#         ('bs_pinstd', np.sum(np.logical_and(dists_mean - dists_std < dists,
#                                             dists < dists_mean + dists_std)) / len(dists))
#     ])


def generate_subsets(set_indices, words):
    unique_indices = {
        s + '-unique': [i for i in indices if i not in
                        set(chain(*[vs for k, vs in set_indices.items() if k != s]))]
        for s, indices in set_indices.items()
    }
    if len(set_indices) > 2:
        common_indices = {
            s + '-common': [i for i in indices if i not in unique_indices[s + '-unique']]
            for s, indices in set_indices.items()
        }
    else:
        common_indices = {}
    intersections = {
        '{}-{}'.format(s1, s2):
        sorted(set(set_indices[s1]) & set(set_indices[s2]))
        for s1, s2 in combinations(sorted(set_indices.keys()), 2)
    }
    intersections = {k: v for k, v in intersections.items() if v}
    set_indices.update(unique_indices)
    set_indices.update(common_indices)
    set_indices.update(intersections)


def main():
    args = parse_arguments()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')

    words, vectors, sets = read_stuff(args.vector_file, args.bev, True)
    vectors = np.asarray(vectors)  # Miniball doesn't work on matrices
    set_indices = OrderedDict((s, []) for s in sets.keys())
    orig_sets = list(set_indices.keys())
    print(orig_sets)

    for i, word in enumerate(words):
        for s, swords in sets.items():
            if word in swords:
                set_indices[s].append(i)

    if args.subsets:
        generate_subsets(set_indices, words)

    centroids = np.zeros((len(orig_sets), vectors.shape[1]), dtype=vectors.dtype)
    for s, indices in set_indices.items():
        v = vectors[indices]
        logging.debug('Computing centroid stats for set {}'.format(s))
        stats = centroid_distribution(v)
        logging.debug('Done computing centroid stats for set {}'.format(s))
        # logging.debug('Computing bounding sphere for set {}'.format(s))
        # bstats = bounding_sphere(v)
        # logging.debug('Computed bounding sphere for set {}'.format(s))
        centroid = stats.pop('centroid')
        if s in orig_sets:
            centroids[orig_sets.index(s)] = centroid
        # center = bstats.pop('center')
        # stats.update(bstats)
        # stats['cdist'] = angular_distance(
        #     np.array([centroid, center / np.linalg.norm(center)]))[0, 1]
        print('Stats for {}:\n  {}'.format(
            s, '\n  '.join(': '.join(map(str, kv)) for kv in stats.items())))

    # Which centroids do the points lie closest?
    closest_centroid = angular_distance(centroids, vectors).argmin(axis=0)
    closest_matrix = np.zeros((len(orig_sets), len(orig_sets)), dtype=int)
    for i, s in enumerate(orig_sets):
        for k, v in Counter(closest_centroid[set_indices[s]]).items():
            closest_matrix[i, k] = v
    closest_table = pd.DataFrame(data=closest_matrix, index=orig_sets,
                                 columns=['->' + s for s in orig_sets])
    print('Confusion matrix based on centroids:')
    print(closest_table)

    for set_to_write in args.write_real:
        try:
            c = orig_sets.index(set_to_write)
            with open('real_' + set_to_write, 'wt') as outf:
                words_to_print = [
                    words[i]
                    for i in set_indices[set_to_write]
                    if closest_centroid[i] == c
                ]
                print('\n'.join(sorted(words_to_print)), file=outf)
        except ValueError:
            logging.warning('No such set: {}'.format(set_to_write))


if __name__ == '__main__':
    main()
