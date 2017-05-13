#!/usr/bin/env python3
"""Configuration-related functionality."""

from __future__ import absolute_import, division, print_function
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
    elif resource_exists('conf', config_file):
        return resource_filename('conf', config_file)
    else:
        raise ValueError('Could not find configuration file {}'.format(config_file))
