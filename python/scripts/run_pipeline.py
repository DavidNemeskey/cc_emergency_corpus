#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Runs a pipeline specified as a JSON file on files in a directory."""

from __future__ import absolute_import, division, print_function
import argparse
import copy
import json
import os
import os.path as op
from queue import Empty

from cc_emergency.functional.core import Pipeline, create_resource, build_pipeline
from cc_emergency.utils import openall, run_queued, setup_queue_logger
from cc_emergency.utils.config import get_config_file


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Runs a pipeline specified as a JSON file on files in a '
                    'directory.')
    parser.add_argument('--configuration', '-c', required=True,
                        help='the JSON configuration file. It should store an '
                             'object with the following two keys: pipeline -- '
                             'a list of resource object descriptors (class, '
                             'args and kwargs), (the transforms augmented with '
                             'a "connection" key whose value is either "map" '
                             'or "filter") and reducer -- a resource '
                             'objet descriptor for the final reducer, if '
                             'needed.')
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


def process_file(configuration, queue, logging_level=None, logging_queue=None):
    logger = setup_queue_logger(logging_level, logging_queue, 'cc_emergency')
    try:
        while True:
            try:
                infile, outfile = queue.get_nowait()
                substitutions = {'%input': infile, '%output': outfile}
                resources = [create_resource(desc, **substitutions) for desc in
                             configuration['pipeline']]
                connections = [desc.get('connection') for desc
                               in configuration['pipeline']][1:-1]
                pipeline = Pipeline(*resources)
                with pipeline:
                    collector, pipe = build_pipeline(resources, connections)
                    logger.info('Started processing {}'.format(infile))
                    collector(pipe)
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
    with openall(get_config_file(args.configuration)) as inf:
        configuration = json.load(inf)
    os.nice(20)  # Play nice

    params = [copy.deepcopy(configuration) for _ in range(args.processes)]
    source_target_files = source_target_file_list(args.input_dir, args.output_dir)
    res = run_queued(process_file, params, args.processes,
                     source_target_files, args.log_level)


if __name__ == '__main__':
    main()
