#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Defines the streams classes that can be used to implement functional data
transformation schemes, such as map-reduce.

The Source implements __iter__ and Transform and Collector implement __call__,
so it is very easy to mix regular Python functions into the pipeline.

TODO: check out PyFunctional. It seems to have implemented this already, but
      it seems to store everything in memory, which might be suboptimal with
      huge datasets.
"""


class Resource(object):
    """
    The base class for the processing steps in the pipeline. Provides functions
    to initialize and clean up the underlying resources.
    """
    def __enter__(self):
        """
        Initializes any resources the object might use. This should be
        done here so that it is only run once in a multiprocessing setting.
        Exceptions should be thrown here instead of in the constructor.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleans up the resources."""
        return False


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
        return self(it)

    def __call__(self, param):
        raise NotImplementedError(
            "__call__() is not implemented in " + self.__class__.__name__)
