#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Embedding vector input-output functions."""

import logging

import numpy as np
from scipy.sparse import csr_matrix, issparse

from cc_emergency.utils import openall
from cc_emergency.utils.scipy_ext import toarray


def write_vectors(words, vectors, vectors_file):
    """
    Writes the vectors to vectors_file. The format depends on the file name
    extension (see read_vectors for more information).
    """
    if vectors_file.endswith('.npz'):
        if issparse(vectors):
            sparse = csr_matrix(vectors)
            np.savez(vectors_file, words=words, vectors_data=sparse.data,
                     vectors_indices=sparse.indices,
                     vectors_indptr=sparse.indptr, vectors_shape=sparse.shape)
        else:
            np.savez(vectors_file, words=words, vectors=vectors)
    else:
        with openall(vectors_file, 'wt') as outf:
            for i, word in enumerate(words):
                print(word, ' '.join(map(str, toarray(vectors[i]))), file=outf)


def read_vectors(vectors_file, normalize=False,
                 dimension=0, keep_words=frozenset()):
    """
    Reads the vectors in vectors_file and returns the list of words and X
    (num_vec x vec_dim).

    This function supports several formats:
    - GloVe .txt format (.txt or .gz)
    - dense .npz format (with 'words' and 'vectors' keys)
    - sparse .npz format (with 'words', 'vectors_data', 'vectors_indices',
                          'vectors_indptr' and 'vectors_shape').

    @param normalize if @c True, all vectors are normalized to unit L2 length.
    @param dimension if not @c 0, the length of the vectors is validated and
                     only those are kept whose length equal to this number.
    @param keep_words if specified, only words in this list are kept.
    """
    def read_text_vectors():
        unreadable, wrong_length = 0, 0
        # 'rb' so that we can catch encoding errors per line
        with openall(vectors_file, 'rb') as inf:
            words, Xrows = [], []
            for line_no, line in enumerate(inf, start=1):
                try:
                    word, *vector = line.decode('utf-8').strip().split(' ')
                except:
                    logging.exception('Error in line {}'.format(line_no))
                    unreadable += 1
                    continue
                if dimension and len(vector) != dimension:
                    wrong_length += 1
                    continue
                if not keep_words or word in keep_words:
                    words.append(word)
                    Xrows.append(list(map(float, vector)))
            logging.info(
                '{} lines; unreadable: {}, wrong length: {}, kept: {}.'.format(
                    line_no, unreadable, wrong_length, len(words)))
            X = np.matrix(Xrows)
            return words, X

    def read_npz_vectors():
        npz = np.load(vectors_file)
        words = npz['words']
        if 'vectors' in npz:
            X = np.matrix(npz['vectors'])
        else:
            X = csr_matrix((npz['vectors_data'], npz['vectors_indices'],
                            npz['vectors_indptr']), shape=npz['vectors_shape'])
        if keep_words:
            indices = [i for i, w in enumerate(words) if w in keep_words]
            words = words[indices]
            X = X[indices]
        return words, X

    if vectors_file.endswith('.npz'):
        words, X = read_npz_vectors()
    else:
        words, X = read_text_vectors()
    if normalize:
        X = normalize_rows(X)
    return list(words), X


def normalize_rows(X):
    """
    Normalizes the rows of matrix X. If X is sparse, it is converted to a
    csr_matrix.
    """
    if issparse(X):
        logging.debug('Normalizing sparse matrix...')
        X = csr_matrix(X)
        norms = np.array(np.sqrt(X.multiply(X).sum(axis=1)))[:, 0]
        row_indices, _ = X.nonzero()
        X.data /= norms[row_indices]
        logging.debug('...done.')
        X = csr_matrix(X)
        return X
    else:
        logging.debug('Normalizing dense matrix...')
        X = X / np.linalg.norm(X, axis=1)[:, np.newaxis]
        logging.debug('...done.')
        return X


def test():
    words = ['dog', 'cat']
    vectors = np.array([[1, 2], [3, 4]])
    np.savez('dense_test.npz', words=words, vectors=vectors)
    print('saved dense')
    vectors = csr_matrix(vectors)
    np.savez(
        'csr_test.npz', words=words, vectors_data=vectors.data,
        vectors_indices=vectors.indices, vectors_indptr=vectors.indptr,
        vectors_shape=vectors.shape)
    print('saved csr')
    words, vectors = read_vectors('dense_test.npz')
    print('loaded dense ({}):\n{}'.format(type(vectors), vectors))
    for i, word in enumerate(words):
        print(i, word, vectors[i])
    words, vectors = read_vectors('csr_test.npz')
    print('loaded csr ({}):\n{}\n{}'.format(
        type(vectors), vectors, vectors.todense()))
    for i, word in enumerate(words):
        print(i, word, vectors[i].toarray()[0])


if __name__ == "__main__":
    test()
