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
from collections import Counter
import json

from cc_emergency.utils import openall


def parse_arguments():
    parser = ArgumentParser(
        description='Joins TF and DF statistics across fields and stats files.')
    parser.add_argument('freq_file', nargs='+',
                        help='a count statistics file.')
    parser.add_argument('--field', '-f', action='append',
                        help='the fields to aggregate. If not specified, all '
                             'fields are aggregated.')
    return parser.parse_args()


def main():
    args = parse_arguments()

    data = {'TF': Counter(), 'DF': Counter()}
    for f in args.freq_file:
        with openall(f) as inf:
            j = json.load(inf)
            for field, stats in j.items():
                if not args.field or field in args.field:
                    data['TF'].update(stats.get('TF', {}))
                    data['DF'].update(stats.get('DF', {}))
    print(json.dumps(data))


if __name__ == '__main__':
    main()
