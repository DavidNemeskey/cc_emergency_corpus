#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Aggregates dictionaries. Aggregation is done with the + operator, so everything
that supports it (numbers, strings, lists) are valid as value types.
"""

from functools import reduce

from cc_emergency.functional.core import Collector


class DictAggregator(Collector):
    def __init__(self, fields=None):
        """
        The argument fields specifies which fields to aggregate. If None, the
        collected objects themselves are aggregated.
        """
        super(DictAggregator, self).__init__()
        self.fields = fields

    def __call__(self, it):
        if self.fields:
            return self.__collect_fields(it)
        else:
            return self.__collect_obj(it)

    def __collect_obj(self, it):
        return reduce(self.__aggregate, it, {})

    def __collect_fields(self, it):
        collected = {field: {} for field in self.fields}
        for obj in it:
            for field in self.fields:
                self.__aggregate(collected[field], obj.get(field, {}))
        return [collected]

    @staticmethod
    def __aggregate(collected, obj):
        for key, value in obj.items():
            if key in collected:
                if isinstance(value, dict):
                    DictAggregator.__aggregate(collected[key], value)
                else:
                    collected[key] += value
            else:
                collected[key] = value
        return collected


print(DictAggregator(['head'])([
    {'head': {'TF': {'a': 1, 'b': 2}, 'DF': {'a': 1, 'b': 1}}, 'body': {'b': 5}},
    {'head': {'TF': {'b': 1, 'c': 2}, 'DF': {'b': 1, 'c': 1}}, 'body': {'b': 3}},
]))
