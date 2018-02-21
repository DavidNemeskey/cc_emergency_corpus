#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Collection collectors."""

from itertools import islice

from cc_emergency.functional.core import Collector


class ListCollector(Collector):
    """Collects (optionally the first n) elements into a list."""
    def __init__(self, num_records=None):
        super(ListCollector, self).__init__()
        self.num_records = num_records

    def __call__(self, it):
        lst = list(islice(it, self.num_records))
        for _ in it:
            pass
        return lst


class SetCollector(Collector):
    """Collects the elements into a set."""
    def __call__(self, it):
        return set(it)


class Sorter(Collector):
    def __init__(self, fields, num_records=None):
        """
        fields is a list of tuples, where each tuple is contains the following
        information: (field, reverse). If more than one fields are specified,
        the first is the MS. num_records, if specified, limits the number of
        records returned.

        Note that this class keeps all records in memory.
        """
        super(Sorter, self).__init__()
        self.fields = fields
        self.num_records = num_records
        self.logger.info('Num records: {}'.format(self.num_records))

    def __key(self, obj):
        return [-obj.get(f) if r else obj.get(f) for f, r in self.fields]

    def __call__(self, it):
        srt = sorted(it, key=self.__key)
        return srt[:self.num_records] if self.num_records else srt
