#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Collects statistics from the corpus."""

from __future__ import absolute_import, division, print_function
from collections import Counter

from cc_emergency.functional.core import Map


class WC(Map):
    """Counts the number of lines, words and characters in the corpus."""
    def __init__(self, field):
        super(WC, self).__init__()
        self.field = field

    def transform(self, obj):
        field_text = obj.get(self.field)
        if field_text:
            lines = field_text.count('\n')
            if field_text[-1] == '\n':
                lines += 1
            return {
                'lines': lines,
                'words': len(field_text.split()),
                'chars': len(field_text)
            }
        else:
            return {'lines': 0, 'words': 0, 'chars': 0}


class Counts(Map):
    """Word counts in specific fields."""
    def __init__(self, fields):
        super(Counts, self).__init__()
        self.fields = fields

    def transform(self, obj):
        for field in self.fields:
            if field in obj:
                obj['{}_counts'.format(field)] = Counter(field)
        return obj
