#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Runs a pipeline specified as a JSON file on files in a directory."""

from __future__ import absolute_import, division, print_function
from builtins import range
import argparse
from itertools import chain
import json
import os
import os.path as op
from queue import Empty
import re
from string import Template
import sys

from cc_emergency.functional.core import Pipeline, create_resource, build_pipeline
from cc_emergency.utils import openall, run_queued
from cc_emergency.utils import setup_queue_logger, setup_stream_logger
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
    parser.add_argument('--input-dir', '-i', required=True, action='append',
                        help='the input directory.')
    out_group = parser.add_mutually_exclusive_group(required=True)
    out_group.add_argument('--output-dir', '-o',
                           help='the output directory. Should not be specified '
                                'for a reduction.')
    out_group.add_argument('--reduced-file', '-r',
                           help='if a reducer is specified, the result is '
                                'written here).')
    parser.add_argument('--R', '-R', action='append', default=[],
                        help='specifies values for template variables in the '
                             'configuration file. The format is -Rxxx=yyy.')
    parser.add_argument('--processes', '-P', type=int, default=1,
                        help='the number of files to process parallelly.')
    parser.add_argument('--log-level', '-L', type=str, default=None,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()

    if args.reduced_file:
        if not re.search('[.](?:json|tsv)$', args.reduced_file):
            parser.error('The reduced file must either be a .json or a .tsv.')
    return args


def process_file(config_str, queue, logging_level=None, logging_queue=None):
    logger = setup_queue_logger(logging_level, logging_queue, 'cc_emergency')
    results = []
    try:
        # First, the transforms are initialized, only once (see #47)
        configuration = json.loads(config_str)
        transforms = [create_resource(desc) for desc in
                      configuration['pipeline'][1:-1]]
        connections = [desc.get('connection') for desc
                       in configuration['pipeline']][1:-1]
        with Pipeline(*transforms):
            while True:
                try:
                    # Then, the source and collector are initialized per file
                    infile, outfile = queue.get_nowait()
                    configuration = json.loads(Template(config_str).safe_substitute(
                        input=infile, output=outfile))
                    inres = create_resource(configuration['pipeline'][0])
                    outres = create_resource(configuration['pipeline'][-1])
                    with Pipeline(inres, outres):
                        # The whole pipeline -- just map and filter objects
                        resources = [inres] + transforms + [outres]
                        collector, pipe = build_pipeline(resources, connections)
                        logger.info('Started processing {}'.format(infile))
                        res = collector(pipe)
                        results += res
                        logger.info('Done processing {}'.format(infile))
                except Empty:
                    logger.debug('Queue depleted.')
                    logger.debug('Holding {} records'.format(len(results)))
                    return results
                except:
                    logger.exception('Exception in file {}'.format(infile))
    except Exception as e:
        logger.exception('Unexpected exception')
        raise


def source_file_list(source_dir):
    """Returns the source files."""
    return [op.abspath(op.join(d, f))
            for d, _, fs in walk_non_hidden(source_dir) for f in fs]


def target_file_list(source_files, source_dir, target_dir):
    source_dir = op.abspath(source_dir)
    target_dir = op.abspath(target_dir)
    target_files = []
    for sf in source_files:
        sf_rel = sf[len(source_dir):].lstrip(os.sep)
        tf = op.join(target_dir, sf_rel)
        td = op.dirname(tf)
        if not op.isdir(td):
            os.makedirs(td)
        target_files.append(tf)
    return target_files


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


def get_reducer(args, config_str):
    """
    Returns with a reducer and exits if reducer in the configuration file and
    reduced_file are not in accord.
    """
    # Reducer, if requested
    reducer = json.loads(config_str).get('reducer')
    if bool(reducer) != bool(args.reduced_file):
        print('The argument --reduced-file is only valid when a reducer is '
              'specified in the configuration file, and vice versa.')
        sys.exit(1)
    if reducer:
        return create_resource(reducer)
    else:
        return None


def write_json(it, outf):
    """Writes the contents of it to outf as json lines."""
    for obj in it:
        print(json.dumps(obj), file=outf)


def write_tsv(it, outf):
    """Writes the contents of it to outf as tsv lines."""
    for obj in it:
        if isinstance(obj, list):
            print('\t'.join(obj), file=outf)
        else:
            print(obj, file=outf)


def main():
    args = parse_arguments()
    setup_stream_logger(args.log_level, 'cc_emergency')  # For logging in the collectors
    os.nice(20)  # Play nice

    with openall(get_config_file(args.configuration)) as inf:
        config_str = inf.read()
    replacements = dict(r.split('=', 1) for r in args.R)
    params = [Template(config_str).safe_substitute(replacements, process=p)
              for p in range(args.processes)]
    reducer = get_reducer(args, params[0])

    source_files, target_files = [], []
    for input_dir in args.input_dir:
        current_sources = source_file_list(input_dir)
        source_files.extend(current_sources)
        if not reducer:
            target_files.extend(target_file_list(
                current_sources, input_dir, args.output_dir))
        else:
            target_files.extend([None for _ in current_sources])
    source_target_files = zip(source_files, target_files)

    res = run_queued(process_file, params, args.processes,
                     source_target_files, args.log_level)
    if reducer:
        ofn = write_json if args.reduced_file.endswith('.json') else write_tsv
        with openall(args.reduced_file, 'wt') as outf, reducer:
            ofn(reducer(chain(*res)), outf)


if __name__ == '__main__':
    main()
