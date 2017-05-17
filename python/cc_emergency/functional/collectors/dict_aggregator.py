#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Aggregates dictionaries. Aggregation is done with the + operator, so everything
that supports it (numbers, strings, lists) are valid as value types.
"""

from cc_emergency.functional.core import Collector


class DictAggregator(Collector):
    def __init__(self, fields=None):
        """
        The argument fields specifies which fields to aggregate. If None, the
        collected objects themselves are aggregated.
        """
        self.fields = fields

    def __call__(self, it):
        if self.fields:
            return self.__collect_fields(it)
        else:
            return self.__collect_obj(it)

    def __collect_obj(self, it):
        collected = {}
        for obj in it:
            self.__aggregate(collected, obj)
        return collected

    def __collect_fields(self, it):
        collected = {field: {} for field in self.fields}
        for obj in it:
            for field in self.fields:
                self.__aggregate(collected[field], obj.get(field, {}))
        return collected

    @staticmethod
    def __aggregate(collected, obj):
        for key, value in obj.items():
            if key in collected:
                collected[key] += value
            else:
                collected[key] = value
