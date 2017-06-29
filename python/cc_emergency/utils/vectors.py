#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Word vector-related functions."""

from __future__ import absolute_import, division, print_function
from itertools import groupby
import logging
import math

import numpy as np
from scipy.sparse import spmatrix
from sklearn import manifold


def compute_mds(vectors, dist_type, processes=1):
    """
    Uses metric multidimensional scaling with angular distance to map the
    points in vectors to two dimensions.
    """
    np.set_printoptions(threshold=np.inf)
    if dist_type.lower().startswith('euc'):
        mds = manifold.MDS(metric=True, n_jobs=processes)
        X = vectors
    elif dist_type.lower().startswith('cos'):
        mds = manifold.MDS(metric=True, n_jobs=processes,
                           dissimilarity='precomputed')
        X = angular_distance(vectors)
    else:
        raise ValueError('dist_type must be euc or cos')

    results = mds.fit(X)
    return results.embedding_


def angular_distance(vectors1, vectors2=None):
    """
    Computes the angular distance between two sets of vectors (or one, if the
    second is omitted). Note that the result is only meaningful if the matrix
    has an L2 row norm of 1.
    """
    vectors1 = vectors1.astype(np.float64, copy=False)
    if vectors2 is None:
        vectors2 = vectors1
    else:
        vectors2 = vectors2.astype(np.float64, copy=False)
    return np.arccos(np.clip(vectors1.dot(vectors2.T), -1, 1)) / np.pi


def emscan_first(words, vectors, initial, min_similarity=0.5, graph=None):
    """
    A dictionary expansion algorithm that works similarly to DBSCAN. Starting
    from an initial cluster, it iteratively adds points (words) to it
    - whose similarity with a word already in the cluster is above
      min_similarity;
    - the first neighbor of a candidate must already be in the cluster
      (yes, this is too strong, as close pairs that are nevertheless close to
      the cluster are not selected).

    Note that initial is a list of indices.

    Graph is a networkx DiGraph. If specified, it is used to record which
    nodes attracted which into the cluster.
    """
    words = np.asarray(words)
    indices = initial
    sindices = set(indices)

    cluster = vectors[indices]
    dists = vectors.dot(cluster.T)
    dists = np.where(dists >= min_similarity, dists, 0)

    candidate_indices = np.array(
        [k for k, _ in groupby(i for i in dists.nonzero()[0]
                               if i not in sindices)]
    )
    logging.debug('Found {} candidate words'.format(len(candidate_indices)))
    #     ', '.join(words[candidate_indices])))

    cdists = vectors[candidate_indices].dot(vectors.T)
    cdists = np.where(cdists >= min_similarity, cdists, 0)
    for i, ri in enumerate(candidate_indices):
        cdists[i, ri] = 0
    selected = {candidate_indices[i]: mi for i, mi
                in enumerate(np.argmax(cdists, axis=1)) if mi in indices}
    graph.add_edges_from([(words[k], words[v]) for k, v in selected.items()])
    selected_indices = sorted(set(selected.keys()))
    logging.debug('Selected words: {}'.format(
        ', '.join(words[selected_indices])))

    return list(indices) + list(selected_indices)


def emscan_dcg(words, vectors, initial, min_similarity=0.5, dcg_length=5,
               min_dcg=1):
    """
    A dictionary expansion algorithm that works similarly to DBSCAN. Starting
    from an initial cluster, it iteratively adds points (words) to it
    - whose similarity with a word already in the cluster is above
      min_similarity;
    - the first neighbor of a candidate must already be in the cluster
      (yes, this is too strong, as close pairs that are nevertheless close to
      the cluster are not selected).

    Note that initial is a list of indices.

    Graph is a networkx DiGraph. If specified, it is used to record which
    nodes attracted which into the cluster. Note that here it is not a tree.
    """
    def dcg(l):
        return l[0] + sum(l[i] / math.log(i + 1, 2) for i in range(1, len(l)))

    words = np.asarray(words)
    indices = initial
    sindices = set(indices)

    cluster = vectors[indices]
    dists = vectors.dot(cluster.T)
    dists = np.where(dists >= min_similarity, dists, 0)

    candidate_indices = np.array(
        [k for k, _ in groupby(i for i in dists.nonzero()[0]
                               if i not in sindices)]
    )
    logging.debug('Candidate words: {}'.format(
        ', '.join(words[candidate_indices])))

    sims = similarities(words, vectors, vectors[candidate_indices],
                        min_similarity, dcg_length + 1, return_words=False)
    # similarities() leaves the original word in the list
    sims = [dcg([w in sindices for w, _ in tuples if w != candidate_indices[r]])
            for r, tuples in enumerate(sims)]
    selected_indices = [candidate_indices[r] for r, dcg_value in enumerate(sims)
                        if dcg_value >= min_dcg]
    logging.debug('Selected words: {}'.format(
        ', '.join(words[selected_indices])))

    return list(indices) + list(selected_indices)


def emscan(words, vectors, initial, min_similarity=0.5, cluster_ratio=0.5):
    """
    A dictionary expansion algorithm that works similarly to DBSCAN. Starting
    from an initial cluster, it iteratively adds points (words) to it
    - whose similarity with a word already in the cluster is above
      min_similarity;
    - the ratio of whose neighbors that are already in the cluster is above
      cluster_ratio.

    Note that initial is a list of indices.
    """
    words = np.asarray(words)
    indices = initial
    sindices = set(indices)

    cluster = vectors[indices]
    dists = vectors.dot(cluster.T)
    dists = np.where(dists >= min_similarity, dists, 0)

    candidate_indices = np.array(
        [k for k, _ in groupby(i for i in dists.nonzero()[0]
                               if i not in sindices)]
    )
    # candidate_words = words[candidate_indices]
    # logging.debug('Candidate words: {}'.format(', '.join(candidate_words)))
    return candidate_indices


def similarities(words, vectors, queries, min_similarity, k,
                 freqs=None, min_freq=0, return_words=True):
    """
    Computes k-NN, based on cosine similarity in an embedding.
    Queries is a matrix, so that more than one neighbor can be computed.
    Returns a [[(word, distance)]]. Parameters:
    - words, vectors: the embedding
    - queries: described above
    - min_similarity: similarities below this threshold are not registered
    - k: the k in k-NN
    - freqs, min_freq: word frequency dictionary and threshold. Optional.
    - return_words: if True (the default), word-distance pairs are returned;
                    otherwise index-distance tuples.
    """
    dists = vectors.dot(queries.T)
    if isinstance(dists, spmatrix):
        dists = dists.todense()
    dists = np.asarray(dists.T)  # Change to rows + array for easier handling
    sorted_dists = np.argsort(dists, axis=1)
    best_indices = sorted_dists[:, ::-1][:, :k]
    neighbors = [list(filter(lambda ws: ws[1] >= min_similarity,
                             [(w, dists[r, w]) for w in row]))
                 for r, row in enumerate(best_indices)]
    if freqs is not None:
        neighbors = [
            list(filter(lambda ws: freqs[words[ws[0]]] >= min_freq, row))
            for row in neighbors]
    if return_words:
        return [[(words[w], d) for w, d in row] for row in neighbors]
    return neighbors
