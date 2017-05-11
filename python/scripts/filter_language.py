#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Filters the corpus for language."""

from __future__ import absolute_import, division, print_function
import argparse
import os
from queue import Empty

from cc_emergency.utils import openall
from cc_emergency.utils import run_queued, setup_queue_logger
from cc_emergency.xml import parse_xml


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

    return args


def process_file(language, queue, logging_level=None, logging_queue=None):
    logger = setup_queue_logger(logging_level, logging_queue)
    try:
        while True:
            try:
                infile, outfile = queue.get_nowait()
                logger.info('Started processing {}'.format(infile))
                with openall(infile, 'rb') as inf:
                    doc_it = parse_xml(inf, True)
                    header = next(doc_it)
                    for doc in doc_it:
                        print(doc['url'])
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


def main():
    args = parse_arguments()
    os.nice(20)  # Play nice

    source_target_files = source_target_file_list(args.source_dir, args.target_dir)
    run_queued(process_file, 'en', args.processes, source_target_files, args.log_level)


if __name__ == '__main__':
    main()
