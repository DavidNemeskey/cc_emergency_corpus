#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Filters the corpus for language."""

from __future__ import absolute_import, division, print_function
import argparse

for doc in parse_xml(input_stream):
    pass  # 1st is header


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Character-based language modeling with RNN.')
    parser.add_argument('--input-dir', '-i', required=True,
                        help='the input directory.')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='the output directory.')
    parser.add_argument('--processes', '-P', type=int, default=1,
                        help='the number of files to process parallelly.')
    args = parser.parse_args()

    # Config file
    pp = partial(config_pp, args=args)
    config, warnings, errors = load_config(
        args.configuration, 'lstm_lm_conf.schema', pp)
    handle_errors(warnings, errors)

    if not args.train and not args.test:
        parser.error('At least one of the train or test sets must be specified.')
    if not args.train and args.reset == 1:
        parser.error('The reset option only works for training.')

    return args, config


def main():
    args = parse_arguments()


if __name__ == '__main__':
    main()
