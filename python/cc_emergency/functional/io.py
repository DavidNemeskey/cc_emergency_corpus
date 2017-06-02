#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""IO classes."""

from __future__ import absolute_import, division, print_function
from collections import OrderedDict
import json
import os

from cc_emergency.utils import openall
from cc_emergency.functional.core import Collector, Resource, Source


# The extensions recognized by the classes here
extensions = set(['json', 'txt'])


class FileWrapper(Resource):
    """Wraps a file stream."""
    def __init__(self, file, mode='rt', *args, **kwargs):
        super(FileWrapper, self).__init__(*args, **kwargs)
        self.file = file
        self.mode = mode

    @staticmethod
    def replace_extension(file_name, extension):
        """
        Replaces the extension of the file in question. Only extensions in
        the global extensions set are replaced.
        """
        parts = file_name.rsplit('.', 1)
        if len(parts) > 1 and parts[1] in extensions and parts[1] != extension:
            return parts[0] + '.' + extension
        else:
            return file_name

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
    def __init__(self, input_file, ordered=True, add_id=None):
        """
        Parameters:
        - input_file the input file
        - ordered whether the order of keys in a dictionary should be kept or
                  not; the default is True
        - add_id if specified, a record id with that name is added to the
                  documents; its value is file_base_name-index.
        """
        super(JsonReader, self).__init__(input_file)
        if ordered:
            self.decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
        else:
            self.decoder = json.JSONDecoder()
        self.add_id = add_id

    def __iter__(self):
        if self.add_id:
            base_name = os.path.basename(self.file)
        for line_no, line in enumerate(self.stream):
            doc = self.decoder.decode(line)
            if self.add_id:
                doc[self.add_id] = '{}-{}'.format(base_name, line_no)
            yield doc


class JsonWriter(Collector, FileWrapper):
    """Writes a text file that has a JSON object on each line."""
    def __init__(self, output_file):
        super(JsonWriter, self).__init__(
            self.replace_extension(output_file, 'json'), 'wt')

    def __call__(self, it):
        for obj in it:
            print(json.dumps(obj), file=self.stream)
        return []


class TextReader(Source, FileWrapper):
    """Reads a text file into a single document."""
    def __iter__(self):
        yield {'id': os.path.basename(self.file),
               'content': self.stream.read()}
