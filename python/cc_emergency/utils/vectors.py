#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Word vector-related functions."""

from __future__ import absolute_import, division, print_function
from builtins import filter
import sys

import numpy as np
from scipy.sparse import csr_matrix
from sklearn import manifold
from sklearn.preprocessing import normalize as normalize_data

from cc_emergency.utils import openall


def read_vectors(vectors_file, word_filter=None, normalize=True, sparse=False):
    """
    Reads the vectors in vectors_file (txt format) and returns the list of
    words and X (num_vec x vec_dim).

    Parameters:
    - normalize: if True (the default), all vectors are normalized to unit L2
                 length;
    - sparse: if True, a csr matrix is returned.
    """
    words, data = [], []
    if sparse:
        row_ind, col_ind = [], []
    it = __enumerate_vector_lines(vectors_file)
    if word_filter:
        it = filter(lambda wv: wv[0] in word_filter, it)
    for row, word_vector in enumerate(it):
        word, vector = word_vector
        words.append(word)
        row_data = np.array(vector)
        if sparse:
            cols = row_data.nonzero()[0]
            row_ind.extend([row] * len(cols))
            col_ind.extend(cols)
            data.extend(row_data[cols])
        else:
            data.append(row_data)

    if sparse:
        X = csr_matrix((data, (row_ind, col_ind)),
                       shape=(row + 1, len(vector) - 1))
    else:
        X = np.array(data)
    if normalize:
        X = normalize_data(X)
    return words, X


def __enumerate_vector_lines(vectors_file):
    """Reads vectors_file and returns the word--float vector pairs in it."""
    with openall(vectors_file, 'rb') as inf:
        for line_no, raw_line in enumerate(inf):
            try:
                if line_no > 0 and line_no % 100000 == 0:
                    print('Line {}'.format(line_no), file=sys.stderr)
                line = raw_line.decode('utf-8')
                fields = line.strip().split(' ')
                yield fields[0], [float(f) for f in fields[1:]]
            except UnicodeDecodeError as ude:
                print('Unicode error in line {}: {}\n{}'.format(line_no, ude, line),
                      file=sys.stderr)
            except ValueError as ve:
                print('Error in line {}: {}\n{}'.format(line_no, ve, line),
                      file=sys.stderr)
                raise


def write_vectors(words, vectors, vectors_file):
    """Writes words and vectors to a .txt vector file."""
    with openall(vectors_file, 'wt') as outf:
        for word, vector in zip(words, vectors):
            print('{} {}'.format(word, ' '.join(str(f) for f in vector)),
                  file=outf)


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
