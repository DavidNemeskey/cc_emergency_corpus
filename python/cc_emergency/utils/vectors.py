#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Word vector-related functions."""

from __future__ import absolute_import, division, print_function

import numpy as np
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
