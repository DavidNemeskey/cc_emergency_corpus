#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""NLP-related functionality."""

from __future__ import absolute_import, division, print_function
import re

import nltk

from cc_emergency.utils.config import create_object


class WordFilter(object):
    def valid(self, word):
        raise NotImplementedError('valid() must be implemented')


class StopWordFilter(WordFilter):
    """NLTK-based stop word filter."""
    def __init__(self, language='english'):
        self.language = language
        self.s = nltk.corpus.stopwords.words(language)

    def valid(self, word):
        return word not in self.s


class LongWordFilter(WordFilter):
    """Drops too long words."""
    def __init__(self, length):
        self.length = length

    def valid(self, word):
        return len(word) <= self.length


class AlnumFilter(WordFilter):
    """Checks if there is at least one alphanumeric character in the word."""
    alnum_p = re.compile('[a-zA-Z0-9]')

    def valid(self, word):
        return self.alnum_p.search(word)


class AllFilter(WordFilter):
    """AND between all specified filter (see create_object)."""
    def __init__(self, filter_configs):
        self.filters = [create_object(filter_conf) for filter_conf
                        in filter_configs]

    def valid(self, word):
        return all(filter.valid(word) for filter in self.filters)
