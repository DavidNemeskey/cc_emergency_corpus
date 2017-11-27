#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Adds bigram versions of fields to the documents."""

from itertools import tee
import re

from cc_emergency.functional.core import Map
from cc_emergency.utils import openall

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


class BigramFilter(Map):
    """
    Removes all bigrams from the bigram fields whose parts are not in the
    unigram set provided.
    """
    US_P = re.compile('_')

    def __init__(self, fields, set_file):
        super(BigramFilter, self).__init__()
        self.fields = fields
        with openall(set_file) as inf:
            self.s = set(inf.read().split('\n'))

    def transform(self, obj):
        for field in self.fields:
            if field in obj:
                obj[field] = {
                    bigram: freq for bigram, freq in obj[field].items()
                    if self.has_valid_split(bigram)
                }
        return obj

    def has_valid_split(self, bigram):
        """
        Checks if a (_-joined bigram) has a valid split, i.e. both of its
        components are in the unigram set.
        """
        for w1, w2 in self.all_splits(bigram):
            if w1 in self.s and w2 in self.s:
                return True
        else:
            return False

    @staticmethod
    def all_splits(bigram):
        """Returns all possible splits of a(n underscore-joined) bigram."""
        for m in BigramFilter.US_P.finditer(bigram):
            yield bigram[:m.span()[0]], bigram[m.span()[1]:]


class BigramFilter2(Map):
    """
    Removes all bigrams from the bigram fields whose parts are not in the
    document as unigrams.
    """
    US_P = re.compile('_')

    def __init__(self, fields):
        """fields here is a map: bigram field -> unigram field it is based on."""
        super(BigramFilter2, self).__init__()
        self.fields = fields

    def transform(self, obj):
        for bif, unif in self.fields.items():
            if bif in obj:
                unigrams = obj[unif].keys()
                obj[bif] = {
                    bigram: freq for bigram, freq in obj[bif].items()
                    if self.has_valid_split(bigram, unigrams)
                }
        return obj

    def has_valid_split(self, bigram, unigrams):
        """
        Checks if a (_-joined bigram) has a valid split, i.e. both of its
        components are in the unigram set.
        """
        for w1, w2 in self.all_splits(bigram):
            if w1 in unigrams and w2 in unigrams:
                return True
        else:
            return False

    @staticmethod
    def all_splits(bigram):
        """Returns all possible splits of a(n underscore-joined) bigram."""
        for m in BigramFilter.US_P.finditer(bigram):
            yield bigram[:m.span()[0]], bigram[m.span()[1]:]
