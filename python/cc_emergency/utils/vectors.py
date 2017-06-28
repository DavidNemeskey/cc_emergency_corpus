#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Word vector-related functions."""

from __future__ import absolute_import, division, print_function

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


def similarities(words, vectors, queries, min_similarity, k,
                 freqs=None, min_freq=0):
    """
    Computes k-NN, based on cosine similarity in an embedding.
    Queries is a matrix, so that more than one neighbor can be computed.
    Returns a list of lists. Paramters:
    - words, vectors: the embedding
    - queries: described above
    - min_similarity: similarities below this threshold are not registered
    - k: the k in k-NN
    - freqs, min_freq: word frequency dictionary and threshold. Optional.
    """
    dists = vectors.dot(queries.T)
    if isinstance(dists, spmatrix):
        dists = dists.todense()
    dists = np.asarray(dists.T)  # Change to rows + array for easier handling
    sorted_dists = np.argsort(dists, axis=1)
    best_indices = sorted_dists[:, ::-1][:, :k]
    neighbors = [list(filter(lambda ws: ws[1] >= min_similarity,
                             [(words[w], dists[r, w]) for w in row]))
                 for r, row in enumerate(best_indices)]
    if freqs is not None:
        neighbors = [
            list(filter(lambda ws: freqs[ws[0]] >= min_freq, row))
            for row in neighbors]
    return neighbors
