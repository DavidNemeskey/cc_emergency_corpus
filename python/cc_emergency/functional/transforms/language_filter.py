#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""A language filtering transform."""

import importlib
import logging

from cc_emergency.functional.core import Transform

class LanguageFilter(Transform):
    """Filters objects for language(s)."""
    def __init__(self, fields, languages):
        """
        - fields: either the name of the field on which to perform the language
                  identification, or a list of fields.
        - languages: either the name of a language or a list of languages
        TODO: should break this up to two objects: one that identifies the
              language, and another to filter the object.
        """
        if not isinstance(fields, list):
            fields = [fields]
        if not isinstance(languages, list):
            languages = [languages]
        self.languages = set(languages)
        self.fields = fields

    def __enter__(self):
        try:
            logging.getLogger('cc_emergency.functional').debug(
                'Loading langid...')
            self.langid = importlib.import_module('langid')
            return self
        except ImportError:
            raise ImportError('The langid module is needed for LanguageFilter '
                              'to work.')

    def __call__(self, obj):
        text = '\n'.join(obj.get(field, '') for field in self.fields)
        return self.langid.classify(text)[0] in self.languages
