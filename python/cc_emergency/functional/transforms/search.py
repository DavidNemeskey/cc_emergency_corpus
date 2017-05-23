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
    def __init__(self, field_weights, query=None, query_file=None):
        """
        The semantics of the field_weights dictionary is obvious;
        query can be a dictionary of {word: weight}, or a list, in which case
        all weights are 1. query_file is a tsv, with one or two columns; these
        two options correspond to the list / dict distinction above. The two
        arguments cannot be specified at the same time.
        """
        super(Search, self).__init__()
        if query and query_file:
            raise ValueError(
                'Only one of query and query_file can be specified.')
        if not query and not query_file:
            raise ValueError('Either query or query_file must be specified.')
        if query_file:
            with openall(query_file, 'rt') as inf:
                query = [l.strip().split('\t') for l in inf]
                if len(query[0]) == 2:
                    query = dict(query)
        self.query = {w: 1 for w in query} if isinstance(query, list) else query
        self.field_weights = field_weights

    def transform(self, obj):
        score = 0
        for field, weight in self.field_weights.items():
            obj_field = obj.get(field)
            if obj_field:
                for qword, qweight in self.query.items():
                    score += obj_field.get(qword, 0) * weight * qweight
        # Python 3.5+: return {**obj, **{'score': score}}
        doc = copy.copy(obj)
        doc['score'] = score
        return doc
