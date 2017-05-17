#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Sorts the documents, based on the field specified by the user."""

from cc_emergency.functional.core import Collector


class Sorter(Collector):
    def __init__(self, fields):
        """
        fields is a list of tuples, where each tuple is contains the following
        information: (field, reverse). If more than one fields are specified,
        the first is the MS.

        Note that this class keeps all records in memory.
        """
        self.fields = fields

    def __key(self, obj):
        return (-obj.get(f) if r else obj.get(f) for f, r in self.fields)

    def __call__(self, it):
        return sorted(it, key=self.__key)
