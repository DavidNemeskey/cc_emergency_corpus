#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""IO classes."""

from __future__ import absolute_import, division, print_function
from collections import OrderedDict
import json

from cc_emergency.utils import openall
from cc_emergency.functional.core import Collector, Resource, Source


class FileWrapper(Resource):
    """Wraps a file stream."""
    def __init__(self, file, mode='rt', *args, **kwargs):
        super(FileWrapper, self).__init__(*args, **kwargs)
        self.file = file
        self.mode = mode

    def __enter__(self):
        """Opens the file."""
        self.stream = openall(self.file, mode=self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the input stream."""
        self.stream.close()
        return False


class JsonReader(Source, FileWrapper):
    """Reads a text file that has a JSON object on each line."""
    def __init__(self, input_file, ordered=True):
        """
        Parameters:
        - input_file the input file
        - ordered whether the order of keys in a dictionary should be kept or
                  not; the default is True.
        """
        super(JsonReader, self).__init__(input_file)
        if ordered:
            self.decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
        else:
            self.decoder = json.JSONDecoder()

    def __iter__(self):
        for line in self.stream:
            yield self.decoder.decode(line)


class JsonWriter(Collector, FileWrapper):
    """Writes a text file that has a JSON object on each line."""
    def __init__(self, output_file):
        super(JsonWriter, self).__init__(output_file, 'wt')

    def __call__(self, it):
        for obj in it:
            print(json.dumps(obj), file=self.stream)
