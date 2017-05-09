#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Corpus reader for the new Reuters corpus."""

from __future__ import absolute_import, division, print_function

from lxml import etree


def parse_xml(input_stream, header=True):
    """
    Parses the Common Crawl XML created by the java part. A generator; the
    header is yielded first, if so requested (the default).
    """
    if header:
        yield input_stream.readline()

    doc, in_doc = None, False
    for event, node in etree.iterparse(input_stream, huge_tree=True,
                                       events=['start', 'end'],
                                       resolve_entities=False):
        if event == 'start':
            if node.tag == 'document':
                doc, in_doc = {}, True
        if event == 'end':
            if node.tag == 'document':
                yield doc
                in_doc = False
            elif in_doc:  # Should be a superfluous check
                doc[node.tag] = node.text
