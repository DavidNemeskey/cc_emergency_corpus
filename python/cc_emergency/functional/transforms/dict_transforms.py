#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Deletes fields from a document."""

from __future__ import absolute_import, division, print_function

from cc_emergency.functional.core import Filter, Map
from cc_emergency.utils import openall


class DeleteFields(Map):
    """Deletes fields from a document."""
    def __init__(self, fields):
        super(DeleteFields, self).__init__()
        self.fields = fields

    def transform(self, obj):
        return {k: v for k, v in obj.items() if k not in self.fields}


class RetainFields(Map):
    """Retains selected fields of a document, dropping all the rest."""
    def __init__(self, fields):
        super(RetainFields, self).__init__()
        self.fields = fields

    def transform(self, obj):
        return {k: v for k, v in obj.items() if k in self.fields}


class FilterEmpty(Filter):
    """
    Filters empty records: if none of the specified fields contain data, the
    record is dropped.
    """
    def __init__(self, fields):
        super(FilterEmpty, self).__init__()
        self.fields = fields

    def transform(self, obj):
        return any(field in obj and obj[field] for field in self.fields)


class FilterDictField(Map):
    """
    Filters a dictionary field by a lambda expression. The latter consists of
    a single statement that returns a boolean value. The only variables
    available to it are k and v, and the set s that results from reading
    set_file.
    """
    def __init__(self, field, function, set_file=None):
        self.field = field
        self.function = compile(function, '<string>', 'eval')
        if set_file:
            with openall(set_file) as inf:
                self.s = set(inf.read().split('\n'))
        else:
            self.s = None

    def transform(self, obj):
        if self.field in obj:
            obj[self.field] = {k: v for k, v in obj[self.field].items()
                               if eval(self.function,
                                       {'k': k, 'v': v, 's': self.s})}
        return obj
