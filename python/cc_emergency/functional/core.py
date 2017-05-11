#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Defines the streams classes that can be used to implement functional data
transformation schemes, such as map-reduce.

The names of the classes are influenced by the Java Stream framework, but this
is only "skin-deep"; the user should not expect that the classes here work in
the same way as their Java not-counterparts.

TODO: check out PyFunctional. It seems to have implemented this already, but
      it seems to store everything in memory, which might be suboptimal with
      huge datasets.
"""


class Stream(object):
    """
    An iterator that defines functions map and filter as convenience.

    NOTE: do we need this?
    """
    def __init__(self, it):
        self.it = it

    def map(self, transform):
        return map(transform, self.it)

    def filter(self, transform):
        return filter(transform, self.it)


class Resource(object):
    """
    The base class for the processing steps in the pipeline. Provides functions
    to initialize and clean up the underlying resources.
    """
    def initialize(self):
        """
        Initializes any resources the object might use. This should be
        done here so that it is only run once in a multiprocessing setting.
        Exceptions should be thrown here instead of in the constructor.
        """
        pass

    def cleanup(self):
        """The opposite of initialize()."""
        pass


class Source(Resource):
    """
    Produces an iterable. Each transformation pipeline starts with a Source.
    """
    def __iter__(self):
        raise NotImplementedError(
            "__iter__() is not implemented in " + self.__class__.__name__)


class Transform(Resource):
    """
    A single transformation. map() and filter() call this function with a
    different purpose.
    """
    def __call__(self, param):
        raise NotImplementedError(
            "__call__() is not implemented in " + self.__class__.__name__)


class Collector(Resource):
    """
    Collects the iterable presented to it. This is a terminal operation, as it
    returns a single value, if any.
    """
    def collect(self, it):
        raise NotImplementedError(
            "collect() is not implemented in " + self.__class__.__name__)
