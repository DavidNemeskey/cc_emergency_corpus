#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Deletes fields from a document."""

from __future__ import absolute_import, division, print_function
import json

from cc_emergency.functional.core import Filter, Map
from cc_emergency.utils import openall


class FilterKeys(Map):
    """Ancestor class for Delete/RetainFields."""
    def __init__(self, fields):
        super(FilterKeys, self).__init__()
        self.fields = fields

    def transform(self, obj):
        new_obj = type(obj)()
        for k, v in obj.items():
            if self.condition(k):
                new_obj[k] = v
        return new_obj

    def condition(self, key):
        """If true, key is kept in the dictionary."""
        raise NotImplementedError('condition must be implemented.')


class DeleteFields(FilterKeys):
    """Deletes fields from a document."""
    def condition(self, key):
        return key not in self.fields


class RetainFields(Map):
    """Retains selected fields of a document, dropping all the rest."""
    def condition(self, key):
        return key in self.fields


class LambdaFilterBase(object):
    """
    Initialization for lambda expression-based filters. It reads the expression
    and an optional set_file argument.
    """
    def __init__(self, expression, set_file=None, *args, **kwargs):
        super(LambdaFilterBase, self).__init__(*args, **kwargs)
        self.expression = compile(expression, '<string>', 'eval')
        if set_file:
            with openall(set_file) as inf:
                self.s = set(inf.read().split('\n'))
        else:
            self.s = None


class FilterDocument(Filter, LambdaFilterBase):
    """
    Filters a document by a lambda expression.  The latter consists of
    a single statement that returns a boolean value. The only variables
    available to it are obj, and the set s that results from reading
    set_file.
    """
    def transform(self, obj):
        return eval(self.expression, {'obj': obj, 's': self.s})


class FilterEmpty(FilterDocument):
    """
    Filters empty records: if none of the specified fields contain data, the
    record is dropped.
    """
    def __init__(self, fields):
        # JSON's list format is the same as Python's
        super(FilterEmpty, self).__init__(
            'any(field in obj and obj[field] for field in set({}))'.format(
                json.dumps(fields)))


class FilterDictField(Map, LambdaFilterBase):
    """
    Filters a dictionary field by a lambda expression. The latter consists of
    a single statement that returns a boolean value. The only variables
    available to it are k and v, and the set s that results from reading
    set_file.
    """
    def __init__(self, field, expression, set_file=None):
        super(FilterDictField, self).__init__(expression, set_file)
        self.field = field

    def transform(self, obj):
        if self.field in obj:
            obj[self.field] = {k: v for k, v in obj[self.field].items()
                               if eval(self.expression,
                                       {'k': k, 'v': v, 's': self.s})}
        return obj
