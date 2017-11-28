#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Statistics."""

from functools import reduce
from operator import add

from cc_emergency.functional.core import Collector


class DocCount(Collector):
    """Counts the number of documents."""
    def __init__(self):
        super(DocCount, self).__init__()

    def __call__(self, it):
        return sum(1 for _ in it)


class Sum(Collector):
    """Sums ints."""
    def __call__(self, it):
        return reduce(add, it)
