#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Samples the text from JSON files and writes them to a directory one file per
text. Created to "interface" with Termolator.
"""

from __future__ import absolute_import, division, print_function
import argparse
import json
import os
import os.path as op
import random

from cc_emergency.utils import openall


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Samples the text from JSON files and writes them to a '
                    'directory one file per text. Created to "interface" with '
                    'Termolator.')
    parser.add_argument('--input-file', '-i', required=True, action='append',
                        help='the input file(s).')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='the input file(s).')
    parser.add_argument('--field', '-f', required=True,
                        help='the field to extract from the JSON.')
    parser.add_argument('--ratio', '-r', default=1.0, type=float,
                        help='the ratio of documents to keep [1.0].')
    parser.add_argument('--number', '-n', default=None, type=int,
                        help='the number of documents to keep [all].')
    parser.add_argument('--digits', '-d', type=int, default=3,
                        help='the number of digits in the output files\' '
                        'names [3].')
    return parser.parse_args()


def iterate_inputs(input_files, field, ratio):
    for input_file in input_files:
        with openall(input_file) as inf:
            for line in inf:
                obj = json.loads(line)
                if field in obj and random.random() < ratio:
                    yield obj[field]


def main():
    args = parse_arguments()
    os.nice(20)
    random.seed(12345)
    out_file = 'file_{{:0{}}}.txt'.format(args.digits)

    for text_id, text in enumerate(
        iterate_inputs(args.input_file, args.field, args.ratio)
    ):
        with openall(op.join(args.output_dir, out_file.format(text_id)), 'wt') as outf:
            outf.write(text)
        if text_id == args.number:
            break


if __name__ == '__main__':
    main()
