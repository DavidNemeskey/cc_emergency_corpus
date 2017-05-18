#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Defines the classes that can be used to implement functional data
transformation schemes, such as map-reduce.

The Source implements __iter__ and Transform and Collector implement __call__,
so it is very easy to mix regular Python functions into the pipeline.

TODO: check out PyFunctional. It seems to have implemented this already, but
      it seems to store everything in memory, which might be suboptimal with
      huge datasets.
"""

from builtins import filter, map
from contextlib2 import ExitStack
import importlib
import json
import logging


class Resource(object):
    """
    The base class for the processing steps in the pipeline. Provides functions
    to initialize and clean up the underlying resources.
    """
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__()
        self.logger = logging.getLogger(
            self.__class__.__module__ + '.' + self.__class__.__name__)

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
    def __call__(self, obj):
        """
        Wraps transform(). This default implementation catches exceptions and
        returns None if one was raised, so that execution does not stop.
        Subclasses may overrule this behavior by overriding __call__.
        """
        try:
            return self.transform(obj)
        except Exception as e:
            self.logger.exception('Error in document {}'.format(obj))

    def transform(self, obj):
        """This is the functions subclasses should override."""
        raise NotImplementedError(
            "transform() is not implemented in " + self.__class__.__name__)


class Map(Transform):
    """
    A single mapping transformation. Can be used both in map() and filter(),
    but build_pipeline defaults to the former.
    """
    pass


class Filter(Transform):
    """
    A single filtering transformation. Can be used both in map() (mostly for
    mapping to boolean values though) and filter(), but build_pipeline defaults
    to the latter.
    """
    pass


class Collector(Resource):
    """
    Collects the iterable presented to it. This is a terminal operation, so
    theoretically it should return a single value, if any. However, since with
    multiprocessing we need to have a final reduction step anyway, Collectors
    should return a list (or set) of results. In this way, they are more
    similar to Reducers in e.g. Hadoop.
    """
    def collect(self, it):
        return self(it)

    def __call__(self, param):
        raise NotImplementedError(
            "__call__() is not implemented in " + self.__class__.__name__)


class Pipeline(ExitStack):
    """
    Provides context management for Resources. When used in a with statement,
    the managed resources can be bound with "as" in the same order they were
    passed to the constructor."""
    def __init__(self, *resources):
        super(Pipeline, self).__init__()
        if not all(isinstance(r, Resource) for r in resources):
            raise ValueError('Pipeline() only accepts instances of Resource.')
        self.resources = resources

    def __enter__(self):
        for resource in self.resources:
            self.enter_context(resource)
        return self.resources


def create_resource(config):
    """
    Creates a Resource object from the specified configuration dictionary.
    Its format is:

        class: The fully qualified path name.
        args: A list of positional arguments (optional).
        kwargs: A dictionary of keyword arguments (optional).
    """
    try:
        module_name, _, class_name = config['class'].rpartition('.')
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return cls(*config.get('args', []), **config.get('kwargs', {}))
    except Exception as e:
        raise Exception(
            'Could not create resource\n{}'.format(json.dumps(config, indent=4)),
            e
        )


def build_pipeline(resources, connections=None):
    """
    Builds a map / filter pipeline between resources. Resources holds the
    resource objects, connections the 'map' or 'filter' string for each
    connection.
    `len(resources) == len(connections) + 2`, because only the connections
    between the transforms are configurable.
    If the value is None, map or filter will be selected based on the class of
    the Transform (Map or Filter).

    Mapping resources also get a filter around them that drop empty objects.
    This allows mappers to just return nothing for erroneous records and get
    away with it.

    Returns the collector object and the pipeline.
    TODO: this is idiotic.
    """
    if len(resources) != len(connections) + 2:
        raise ValueError(
            'The number of resources ({}) '.format(len(resources)) +
            'and connections ({}) is not '.format(len(connections)) +
            'compatible (r = c + 2).')
    pipe = resources[0]
    for r, c in zip(resources[1:-1], connections):
        if not c:
            if isinstance(r, Map):
                c = 'map'
            elif isinstance(r, Filter):
                c = 'filter'
            else:
                raise ValueError(
                    'No connection specified to resource {}'.format(r))
        if c == 'map':
            pipe = filter(lambda e: e, map(r, pipe))
        else:
            pipe = filter(r, pipe)
    return resources[-1], pipe
