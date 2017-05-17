#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Filters empty records."""

from cc_emergency.functional.core import Filter


class FilterEmpty(Filter):
    """
    Filters empty records: if none of the specified fields contain data, the
    record is dropped.
    """
    def __init__(self, fields):
        self.fields = fields

    def __call__(self, obj):
        return any(field in obj and obj[field] for field in self.fields)
