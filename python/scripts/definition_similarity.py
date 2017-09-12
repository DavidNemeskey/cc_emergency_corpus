#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Judit Acs <judit@sch.bme.hu>
#
# Distributed under terms of the MIT license.

from argparse import ArgumentParser
import logging
import os

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity


class Vocabulary(object):
    """
    Defining vocabulary handler.
    Reads vocabulary, filters stopwords and another arbitrary list of
    words.
    Maps words to indices.
    Creates sparse matrix from definition list. The matrix is filtered
    to the words present in the Vocabulary.
    """
    def __init__(self, vocab_fn, filter_stopwords=False, filter_words=None):
        with open(vocab_fn) as f:
            self.__words = list(set(l.strip() for l in f))
        if filter_stopwords:
            from nltk.corpus import stopwords
            s = stopwords.words('english')
            self.__words = list(filter(lambda x: x not in s, self.__words))
        if filter_words:
            with open(filter_words) as f:
                filt = set(l.strip() for l in f)
            self.__words = list(filter(lambda x: x not in filt, self.__words))
        self.__word_mapping = {}
        for word in self.__words:
            self.__word_mapping.setdefault(word, len(self.__word_mapping))

    @property
    def words(self):
        return self.__words

    def create_definition_matrix(self, definition_list):
        m = sparse.dok_matrix((len(definition_list), len(self.__words)), dtype=np.int8)
        for di, definition in enumerate(definition_list):
            for word in definition:
                if word in self.__word_mapping:
                    m[di, self.__word_mapping[word]] = 1
        return m


class Dictionary(object):
    """
    Dictionary handler class.
    Reads and vectorizes dictionary.
    Finds similar words to an arbitrary list of words based on common
    words in their definitions.
    """
    def __init__(self, dict_fn, vocab):
        self.definitions = {}
        self.__table = pd.read_table(dict_fn)[['headword', 'definition']]
        self.__table = self.__table.fillna("")
        for row in self.__table.iterrows():
            lhs = row[1]['headword']
            rhs = row[1]['definition']
            if lhs in self.definitions:
                i = 2
                while '{0}_{1}'.format(lhs, i) in self.definitions:
                    i += 1
                self.definitions['{0}_{1}'.format(lhs, i)] = set(rhs.strip().split())
            else:
                self.definitions[lhs] = set(rhs.strip().split())
        self.vocab = vocab
        self.definiendum = list(self.definitions.keys())
        self.definition_list = [list(self.definitions[w]) for w in self.definiendum]
        self.matrix = self.vocab.create_definition_matrix(self.definition_list)

    @property
    def self_similarity_matrix(self):
        try:
            return self.__similarity_matrix
        except AttributeError:
            sim = self.vocab.create_definition_matrix(
                self.definition_list)
            self.__similarity_matrix = cosine_similarity(sim)
        return self.__similarity_matrix

    def find_similar(self, words, verbose=False):
        word_l = list(set(words))
        word_l = []
        for word in self.definitions.keys():
            if word.split('_')[0] in words:
                word_l.append(word)
        word_def_list = [self.definitions[w] for w in word_l]
        word_mtx = self.vocab.create_definition_matrix(word_def_list)
        sim = cosine_similarity(word_mtx, self.matrix)
        for i in range(sim.shape[0]):
            left_w = word_l[i]
            for j in range(sim.shape[1]):
                right_w = self.definiendum[j]
                s = sim[i, j]
                if s == 0:
                    continue
                if verbose:
                    common_words = [
                        w for w in self.vocab.words
                        if w in self.definitions[left_w] and
                        w in self.definitions[right_w]
                    ]
                    print('{0}\t{1}\t{2}\t{3}'.format(
                        left_w, right_w, s, ' '.join(common_words)
                    ))
                else:
                    print('{0}\t{1}\t{2}'.format(
                        left_w, right_w, s
                    ))


def parse_args():
    p = ArgumentParser(
        description="""
        Build similarity matrix between definitions,
        using a predefined vocabulary.
        """
    )
    p.add_argument('--vocab', type=str, required=True,
                  help="Defining vocabulary (all other words are be excluded)")
    p.add_argument('--definitions', type=str, required=True,
                   help="Definition files")
    p.add_argument('--find-similar', type=str, required=True,
                   help="Find similar words in dictionary to this list")
    p.add_argument('--filter-stopwords', action='store_true',
                   help="Filter stopwords from definitions")
    p.add_argument('--word-filter', type=str,
                   help="Filter arbitrary list of words from definitions")
    return p.parse_args()


def main():
    logger = logging.getLogger(__name__)
    args = parse_args()
    vocab = Vocabulary(args.vocab, filter_stopwords=args.filter_stopwords,
                       filter_words=args.word_filter)
    logger.info('Vocabulary loaded')
    d = Dictionary(args.definitions, vocab)
    logger.info('Dictionary loaded')
    if os.path.exists(args.find_similar):
        with open(args.find_similar) as f:
            search_for = set(l.strip() for l in f)
    else:
        search_for = set(args.find_similar.split())
    d.find_similar(search_for, verbose=True)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
