#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Reads a JSON-per-line file and creates a .tsv file from a subset of its fields.
"""

from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from contextlib import contextmanager
import json
import sys

from cc_emergency.utils import openall


def parse_arguments():
    parser = ArgumentParser(
        description='Reads a JSON-per-line file and creates a .tsv file from a '
                    'subset of its fields.')
    parser.add_argument('json_file', help='the input JSON file. If -, the '
                                          'input is read from stdin.')
    parser.add_argument('--field', '-f', action='append',
                        help='the field(s) to add to the .tsv.')
    args = parser.parse_args()
    if not args.field:
        parser.error('At least one field must be specified.')
    return args


@contextmanager
def asis(stream):
    yield stream


def main():
    args = parse_arguments()
    infile = args.json_file
    with (openall(infile) if infile != '-' else asis(sys.stdin)) as inf:
        for line in inf:
            j = json.loads(line)
            print('\t'.join(j.get(f, '') for f in args.field))


if __name__ == '__main__':
    main()
