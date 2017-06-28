#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Reads an embedding an lets the user query the nearest neighbors."""
from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from builtins import input
from collections import Counter
from itertools import chain
import logging
import sys

import numpy as np

from cc_emergency.utils.vector_io import read_vectors, normalize_rows
from cc_emergency.utils.vectors import similarities


def parse_arguments():
    parser = ArgumentParser(
        description='Reads an embedding an lets the user query '
                    'the nearest neighbors.')
    parser.add_argument('embedding',
                        help='The embedding file.')
    parser.add_argument('--k', '-k', type=int, default=5,
                        help='The number of neighbors to print. Default is 5.')
    parser.add_argument('--min-similarity', '-s', type=float, default=0,
                        help='The minimum similarity a neighbor must reach to '
                             'be included in the list.')
    parser.add_argument('--normalize', '-n', action='store_true',
                        help='Normalize the vectors to 1 (L2).')
    parser.add_argument('--batch', '-b', action='append', default=[],
                        help='File to batch-process. Can be specified more '
                             'than once. If it is, the interactive phase is '
                             'skipped.\nThe file can contain one word on a '
                             'single line, or a word and the associated '
                             'vector. In the former case, the vector is taken '
                             'from the embedding.')
    parser.add_argument('--dimension', '-d', type=int, default=0,
                        help='The length of the embedding vectors. It is '
                             'inferred from the data, but can be specified, '
                             'in which case vectors with different lengths '
                             'are thrown away. A good way to filter invalid '
                             'data.')
    parser.add_argument('--self-contained', '-S', action='store_true',
                        help='If specified, only the distances between the '
                             'query words themselves are computed. Only valid '
                             'for batch mode.')
    parser.add_argument('--min-freq', '-m', type=int, default=1,
                        help='Do not print neighbors that have a lower '
                             'frequency than this threshold. Requires that '
                             'a frequency list be passed to the script using '
                             '--freq-list or -f')
    parser.add_argument('--freq-list', '-f',
                        help='Read word frequencies from the given file,'
                             'which should be a TAB-separated file with the '
                             'first two columns containing the frequency and '
                             'word form, resprectively. Frequencies can '
                             ' then be used for thresholding '
                             'with the --min-freq option.')
    parser.add_argument('--log-level', '-L', type=str, default='info',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    if args.self_contained and not args.batch:
        parser.error('--self-contained is only valid for batch mode.')
    return args


def interactive_knn(words, vectors, word_index, min_similarity, k, freqs,
                    min_freq):
    try:
        while True:
            word = input('> ')
            if len(word) == 0:
                break
            elif word not in word_index:
                print("Not in the embedding.", file=sys.stderr)
            else:
                # print(word_index[word])
                # row = vectors[word_index[word]]
                neighbors = similarities(
                    words, vectors, vectors[word_index[word]],
                    min_similarity, k, freqs, min_freq)[0]
                # dists = np.dot(vectors, row)
                # sorted_dists = np.argsort(dists)
                # neighbors = filter(lambda ws: ws[1] >= min_similarity,
                #                    [(words[w], dists[w]) for w in
                #                     sorted_dists[::-1][:k]])
                # print(', '.join('{}({})'.format(
                #    w.encode('utf-8'), s) for w, s in neighbors))
                print(', '.join('{} ({})'.format(
                    w, s) for w, s in neighbors))
    except EOFError:
        pass


def batch_knn(words, vectors, word_index, batch_file, min_similarity, k,
              dimension=0, normalize=False, self_contained=False, freqs=None,
              min_freq=0):
    """Executes a batch query. For the batch file format, see above."""
    with open(batch_file) as inf:
        batch = [l.strip().split(maxsplit=1) for l in inf]
        words_only = list(filter(
            lambda b: len(b) == 1 and b[0] in words, batch))
        vectors_too = list(filter(lambda b: len(b) > 1, batch))
        query_words = [w[0] for w in chain(words_only, vectors_too)]
        queries = np.matrix(np.zeros((len(query_words), vectors.shape[1]),
                                     dtype=vectors.dtype))
        for i, word in enumerate(words_only):
            queries[i] = vectors[word_index[word[0]]]
        for i, wv in enumerate(vectors_too):
            queries[len(words_only) + i] = list(map(float, wv[1].split()))
        if normalize:
            queries = normalize_rows(queries)

    neighbors = similarities(query_words if self_contained else words,
                             queries if self_contained else vectors,
                             queries, min_similarity, k, freqs, min_freq)
    for i, neighbor in enumerate(neighbors):
        print('{} '.format(query_words[i]) +
              ', '.join('{}({})'.format(w, s) for w, s in neighbor))


def read_freqs(fn):
    freqs = Counter()
    with open(fn) as f:
        for line in f:
            freq, word = line.strip().split('\t')[:2]
            freqs[word] = int(freq)
    return freqs


if __name__ == '__main__':
    args = parse_arguments()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s - %(levelname)s - %(message)s')

    if args.freq_list is not None:
        logging.info("Reading {}...".format(args.freq_list))
        freqs = read_freqs(args.freq_list)
    else:
        freqs = None
    logging.info("Reading {}...".format(args.embedding))
    words, vectors = read_vectors(
        args.embedding, args.normalize, args.dimension)
    word_index = {word: i for i, word in enumerate(words)}
    logging.info("Done reading embedding.")

    if args.batch:
        for batch in args.batch:
            batch_knn(words, vectors, word_index, batch,
                      args.min_similarity, args.k, args.dimension,
                      args.normalize, args.self_contained, freqs,
                      args.min_freq)
    else:
        interactive_knn(
            words, vectors, word_index, args.min_similarity, args.k, freqs,
            args.min_freq)
