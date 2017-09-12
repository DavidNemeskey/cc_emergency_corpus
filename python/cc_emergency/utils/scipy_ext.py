#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Functions that should be in scipy."""

import numpy as np
from scipy.sparse import issparse


def dot(a, b):
    """A dot product that also works on sparse matrices."""
    if issparse(a):
        return a.dot(b)
    elif issparse(b):
        return b.T.dot(a.T).T
    else:
        return np.dot(a, b)


def toarray(matrix, squeeze=True):
    """
    This is a shame, this should be in scipy. Converts any matrix to ndarray.
    """
    if issparse(matrix):
        A = matrix.toarray()
    elif isinstance(matrix, np.matrix):
        A = matrix.A
    else:
        A = np.asanyarray(matrix)
    return np.squeeze(A) if squeeze else A
