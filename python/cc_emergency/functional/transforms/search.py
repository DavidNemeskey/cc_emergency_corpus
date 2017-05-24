#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Search in documents."""

from __future__ import absolute_import, division, print_function
import copy

from cc_emergency.functional.core import Map
from cc_emergency.utils import openall


class Search(Map):
    """
    Searches in documents with a weighted query. The field searched must be a
    {word: Tf} dictionaries.
    """
    def __init__(self, field_weights, scorer, query=None, query_file=None):
        """
        The semantics of the field_weights dictionary is obvious;
        query can be a dictionary of {word: weight}, or a list, in which case
        all weights are 1. query_file is a tsv, with one or two columns; these
        two options correspond to the list / dict distinction above. The two
        arguments cannot be specified at the same time.

        The scorer is a dictionary: {scorer: tf|okapi, params: {...}}, where the
        params dictionary is only required for okapi.
        """
        super(Search, self).__init__()
        if query and query_file:
            raise ValueError(
                'Only one of query and query_file can be specified.')
        if not query and not query_file:
            raise ValueError('Either query or query_file must be specified.')

        self.field_weights = field_weights
        self.query = self.__read_query(query, query_file)
        self.scorer = self.__get_scorer(scorer)

    def __read_query(self, query=None, query_file=None):
        if query_file:
            with openall(query_file, 'rt') as inf:
                query = [l.strip().split('\t') for l in inf]
                if len(query[0]) == 2:
                    query = dict(query)

        if isinstance(query, list):
            return {w: 1 for w in query}
        else:
            return {w: float(f) for w, f in query.items()}

    def __get_scorer(self, scorer):
        if scorer.get('scorer') == 'okapi':
            return OkapiScorer(**scorer.get('params', {}))
        elif scorer.get('scorer') == 'tf':
            return TFScorer()
        else:
            raise ValueError('Invalid scorer "{}"'.format(scorer.get('scorer')))

    def transform(self, obj):
        score = 0
        for field, weight in self.field_weights.items():
            obj_field = obj.get(field)
            if obj_field:
                score += self.scorer.score(self.query, obj_field) * weight
        # Python 3.5+: return {**obj, **{'score': score}}
        doc = copy.copy(obj)
        doc['score'] = score
        return doc


class Scorer(object):
    """
    Scorer object used by the Search transform. Only implements the TF part
    of the scoring schemes; the IDF part must be computed outside and
    supported to Search as word weights.
    """
    def score(self, query, field):
        """
        Computes the score from the query ({qword: qweight}) and the field
        dictionary ({word: TF}).
        """
        raise NotImplementedError('score must be implented')


class TFScorer(Scorer):
    """Implements a simple TF scheme, i.e. sum(TF_q) for q in query."""
    def score(self, query, field):
        return sum(field.get(qword, 0) * qweight
                   for qword, qweight in query.items())


class OkapiScorer(Scorer):
    """The TF part of Okapi-BM25."""
    def __init__(self, k1, b, avgdl):
        self.k1 = k1
        self.b = b
        self.avgdl = avgdl

    def score(self, query, field):
        denom = self.k1 * (1 - self.b * (1 - sum(field.values()) / self.avgdl))
        score = 0
        for qword, qweight in query.items():
            tf = field.get(qword, 0)
            score += (self.k1 + 1) * tf / (tf + denom) * qweight
        return score
