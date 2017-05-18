#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""A preprocessor that invokes a Stanford CoreNLP server for analysis."""

from __future__ import absolute_import, division, print_function

from cc_emergency.functional.core import Map
from cc_emergency.functional.transforms.corenlp_backend import CoreNLPBackend


class CoreNLP(Map):
    """A Transform that invokes a Stanford CoreNLP server for analysis."""
    def __init__(self, props, fields, max_length=10000):
        """
        Parameters:
        - corenlp_props the properties file for the server (see CoreNLP).
        - fields the fields to parse. Each yields a new field called
                 field + '_corenlp'
        - max_length: the maximum chunk size.
        """
        super(CoreNLP, self).__init__()
        self.corenlp_props = props
        self.fields = fields
        self.max_length = max_length
        self.corenlp = None

    def __enter__(self):
        """
        The CoreNLP server is initialized here so that it is only created once,
        in the processing process, not in the main one.
        """
        if not self.corenlp:
            self.corenlp = CoreNLPBackend(self.corenlp_props)

    def __exit__(self, *args):
        if self.corenlp:
            del self.corenlp
        self.corenlp = None

    def transform(self, obj):
        for field in self.fields:
            if field in obj and obj[field]:
                obj[field + '_corenlp'] = []
                for parsed in self.__parse_with_corenlp(obj[field]):
                    obj[field + '_corenlp'].extend(parsed)
        return obj

    def __parse_with_corenlp(self, text):
        """
        Parses the input with CoreNLP. This generator is called from
        transform(). Reads from the text a batch of lines, and
        yields the parsed data chunk.
        """
        chunk, chunk_len = [], 0
        for txt in text.split('\n'):
            chunk.append(txt)
            chunk_len += len(txt)
            if chunk_len > self.max_length:
                yield self.corenlp.parse('\n'.join(chunk))
                chunk, chunk_len = [], 0
        if chunk:
            yield self.corenlp.parse('\n'.join(chunk))
