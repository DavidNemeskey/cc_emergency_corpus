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
    if dist_type.lower().startswith('euc'):
        mds = manifold.MDS(metric=True, n_jobs=processes)
        X = vectors
    elif dist_type.lower().startswith('cos'):
        mds = manifold.MDS(metric=True, n_jobs=processes,
                           dissimilarity='precomputed')
        X = __angular_distance(vectors)
    else:
        raise ValueError('dist_type must be euc or cos')

    results = mds.fit(X)
    print('Results: {}'.format(results))
    return results.embedding_


def __angular_distance(vectors):
    """Computes the angular distances between the vectors."""
    cosine_similarity = vectors.dot(vectors.T)
    return np.arccos(cosine_similarity) / np.pi
