#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""NLP-related transformations."""

from cc_emergency.functional.core import Map
from cc_emergency.utils.nlp import AllFilter


class FilterFields(Map):
    """Filters the content of select fields using the specified filters."""
    def __init__(self, fields, filters=None):
        super(FilterFields, self).__init__()
        self.fields = fields
        self.filter_confs = filters or []

    def __enter__(self):
        self.filter = AllFilter(self.filter_confs)

    def transform(self, obj):
        for field in self.fields:
            if field in obj:
                obj[field] = [w for w in obj[field] if self.filter.valid(w)]
        return obj
