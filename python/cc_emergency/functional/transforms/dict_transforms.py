#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Deletes fields from a document."""

from __future__ import absolute_import, division, print_function

from cc_emergency.functional.core import Filter, Map


class DeleteFields(Map):
    """Deletes fields from a document."""
    def __init__(self, fields):
        super(self, DeleteFields).__init__()
        self.fields = fields

    def __call__(self, obj):
        return {k: v for k, v in obj.items() if k not in self.fields}


class RetainFields(Map):
    """Retains selected fields of a document, dropping all the rest."""
    def __init__(self, fields):
        super(self, RetainFields).__init__()
        self.fields = fields

    def __call__(self, obj):
        return {k: v for k, v in obj.items() if k in self.fields}


class FilterEmpty(Filter):
    """
    Filters empty records: if none of the specified fields contain data, the
    record is dropped.
    """
    def __init__(self, fields):
        super(self, FilterEmpty).__init__()
        self.fields = fields

    def __call__(self, obj):
        return any(field in obj and obj[field] for field in self.fields)
