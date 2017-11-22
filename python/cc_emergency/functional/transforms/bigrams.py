#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Adds bigram versions of fields to the documents."""

from itertools import tee

from cc_emergency.functional.core import Map

class CreateBigrams(Map):
    """
    Creates bigram versions of selected fields in the document. In order to
    make it easier for text-based tools to handle these fields, the bigrams
    are not tuples, but the two words joined by an underscore.

    The name of the new field will be {field}_bigrams. If it already exists,
    it is left alone, unless the overwrite argument is True.
    """
    def __init__(self, fields, overwrite=False):
        super(CreateBigrams, self).__init__()
        self.fields = fields
        self.overwrite = overwrite

    def transform(self, obj):
        for field in self.fields:
            new_field = '{}_bigrams'.format(field)
            if field in obj:
                if new_field not in obj or self.overwrite:
                    obj[new_field] = ['_'.join(bigram) for bigram in
                                      self.pairwise(obj[field])]
        return obj

    @staticmethod
    def pairwise(iterable):
        """The itertools recipe."""
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)
