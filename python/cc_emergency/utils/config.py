#!/usr/bin/env python3
"""Configuration-related functionality."""

from __future__ import absolute_import, division, print_function
import importlib
import json
import os
from pkg_resources import resource_exists, resource_filename


def get_config_file(config_file):
    """
    Returns the path to the configuration file specified. If there is a file at
    the path specified, it is returned as is; if not, the conf/ directory of the
    installed package is checked. If that fails as well, ValueError is raised.
    """
    if os.path.isfile(config_file):
        return config_file
    elif resource_exists('cc_emergency.conf', config_file):
        return resource_filename('cc_emergency.conf', config_file)
    else:
        raise ValueError('Could not find configuration file {}'.format(config_file))


def create_object(config):
    """
    Creates an object from the specified configuration dictionary.
    Its format is:

        class: The fully qualified path name.
        args: A list of positional arguments (optional).
        kwargs: A dictionary of keyword arguments (optional).
    """
    try:
        module_name, _, class_name = config['class'].rpartition('.')
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return cls(*config.get('args', []), **config.get('kwargs', {}))
    except Exception as e:
        raise Exception(
            'Could not create object\n{}'.format(json.dumps(config, indent=4)),
            e
        )
