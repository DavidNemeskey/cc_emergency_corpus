#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Business vocabulary-related classes."""

from __future__ import absolute_import, division, print_function
import re

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


class GetEntitiesFromConll(object):
    """
    Gets entities (word bursts whose kth CoNLL field matches a regex) from
    CoNLL-formatted data.
    """
    def __init__(self, word_field, type_field, type_regex):
        self.word_field = word_field
        self.type_field = type_field
        self.type_regex = type_regex
        self.p = re.compile(type_regex)

    def get_entities(self, conll):
        wf, tf, p = self.word_field, self.type_field, self.p
        entities = set()
        for sentence in conll:
            entity = []
            for token in sentence:
                if p.match(token[tf]):
                    entity.append(token[wf].lower())
                elif entity:
                    entities.add(tuple(entity))
                    entity = []
            if entity:
                entities.add(tuple(entity))
        return entities


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
                return obj
