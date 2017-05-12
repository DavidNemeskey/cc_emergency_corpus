#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Filters the corpus for language."""

from __future__ import absolute_import, division, print_function
import argparse
import os
import os.path as op
from queue import Empty

from cc_emergency.functional.core import Pipeline
from cc_emergency.functional.io import JsonReader, JsonWriter
from cc_emergency.functional.transforms import LanguageFilter
from cc_emergency.utils import run_queued, setup_queue_logger


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Character-based language modeling with RNN.')
    parser.add_argument('--input-dir', '-i', required=True,
                        help='the input directory.')
    parser.add_argument('--output-dir', '-o', required=True,
                        help='the output directory.')
    parser.add_argument('--processes', '-P', type=int, default=1,
                        help='the number of files to process parallelly.')
    parser.add_argument('--log-level', '-L', type=str, default=None,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()

    return args


def process_file(language, queue, logging_level=None, logging_queue=None):
    logger = setup_queue_logger(logging_level, logging_queue, 'cc_emergency')
    try:
        while True:
            try:
                infile, outfile = queue.get_nowait()
                pipeline = Pipeline(JsonReader(infile),
                                    LanguageFilter('content', 'en'),
                                    JsonWriter(outfile))
                logger.info('Started processing {}'.format(infile))
                with pipeline as (jin, lf, jout):
                    jout(filter(lf, jin))
                logger.info('Done processing {}'.format(infile))
            except Empty:
                logger.debug('Queue depleted.')
                break
            except:
                logger.exception('Exception in file {}'.format(
                    infile))
    except Exception as e:
        logger.exception('Unexpected exception')
        raise


def source_target_file_list(source_dir, target_dir):
    source_dir = op.abspath(source_dir)
    target_dir = op.abspath(target_dir)
    source_files = [op.abspath(op.join(d, f))
                    for d, _, fs in walk_non_hidden(source_dir) for f in fs]
    target_files = []
    for sf in source_files:
        sf_rel = sf[len(source_dir):].lstrip(os.sep)
        tf = op.join(target_dir, sf_rel)
        td = op.dirname(tf)
        if not op.isdir(td):
            os.makedirs(td)
        target_files.append(tf)
    return zip(source_files, target_files)


def walk_non_hidden(directory):
    """Walks directory as os.walk, skipping hidden files and directories."""
    def delete_hidden(lst):
        for i in range(len(lst) - 1, -1, -1):
            if lst[i][0] == '.':
                del lst[i]

    for tup in os.walk(directory):
        dirpath, dirnames, filenames = tup
        delete_hidden(dirnames)
        delete_hidden(filenames)
        yield tup


def main():
    args = parse_arguments()
    os.nice(20)  # Play nice

    source_target_files = source_target_file_list(args.input_dir, args.output_dir)
    run_queued(process_file, 'en', args.processes, source_target_files, args.log_level)


if __name__ == '__main__':
    main()
