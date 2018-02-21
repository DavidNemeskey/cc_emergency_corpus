#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Business vocabulary-related classes."""

from __future__ import absolute_import, division, print_function

from cc_emergency.functional.core import Map
from cc_emergency.utils import openall


class Extractor(Map):
    """
    Extracts documents from a collection that contain at least a certain
    number and type of the keywords provided.
    """
    def __init__(self, keyword_file, min_keywords):
        super(Extractor, self).__init__()
        self.keywords = self.read_kw_file(keyword_file)
        self.min_keywords = min_keywords

    def read_kw_file(self, keyword_file):
        with openall(keyword_file) as inf:
            return set(tuple(line.strip().lower().split('\t')) for line in inf)


class ExtractFromNews(Extractor):
    """Extracts the documents from the news collections."""
    def __init__(self, keyword_file, min_keywords, conll_field):
        super(ExtractFromNews, self).__init__(keyword_file, min_keywords)
        self.conll_field = conll_field

    def transform(self, obj):
        conll = obj.get(self.conll_field)
        if conll:
            doc = set((token[0].lower(), token[2].lower())
                      for sentence in conll for token in sentence)
            intersection = len(doc & self.keywords)
            if intersection >= self.min_keywords:
                obj[self.conll_field + '_match'] = intersection
                yield obj
