#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Joins TF and DF statistics across fields and stats files. This is required
because
1. TF and DF statistics are now per-field
2. Because of bigrams (and multiprocessing) (and NFS), several count files had
to be used to fit in memory.
"""

from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from collections import defaultdict, Counter
import json

from cc_emergency.utils import openall


def parse_arguments():
    parser = ArgumentParser(
        description='Joins TF and DF statistics across fields and stats files.')
    parser.add_argument('freq_file', nargs='+',
                        help='a count statistics file.')
    parser.add_argument('--aggregate', '-a', action='store_true',
                        help='whether to aggregate fields.')
    parser.add_argument('--field', '-f', dest='fields', action='append',
                        help='the fields to aggregate (if -a is present). If '
                             'not specified, all fields are aggregated.')
    args = parser.parse_args()

    if args.fields and not args.aggregate:
        parser.error('-f has no effect if -a is not present.')
    return args


def counters():
    """Default value for defaultdict."""
    return {'TF': Counter(), 'DF': Counter()}


def main():
    args = parse_arguments()

    data = counters() if args.aggregate else defaultdict(counters)
    for f in args.freq_file:
        with openall(f) as inf:
            j = json.load(inf)
            for field, stats in j.items():
                if args.aggregate:
                    if not args.fields or field in args.fields:
                        data['TF'].update(stats.get('TF', {}))
                        data['DF'].update(stats.get('DF', {}))
                else:
                    data[field]['TF'].update(stats.get('TF', {}))
                    data[field]['DF'].update(stats.get('DF', {}))
    print(json.dumps(data))


if __name__ == '__main__':
    main()
