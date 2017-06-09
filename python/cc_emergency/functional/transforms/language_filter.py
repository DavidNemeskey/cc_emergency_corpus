#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Language / domain filtering transforms."""

import importlib

import tldextract

from cc_emergency.functional.core import Filter


class LanguageFilter(Filter):
    """Filters objects for language(s)."""
    def __init__(self, fields, languages):
        """
        - fields: either the name of the field on which to perform the language
                  identification, or a list of fields.
        - languages: either the name of a language or a list of languages
        TODO: should break this up to two objects: one that identifies the
              language, and another to filter the object.
        """
        super(LanguageFilter, self).__init__()
        if not isinstance(fields, list):
            fields = [fields]
        if not isinstance(languages, list):
            languages = [languages]
        self.languages = set(languages)
        self.fields = fields

    def __enter__(self):
        try:
            self.logger.debug('Loading langid...')
            self.langid = importlib.import_module('langid')
            return self
        except ImportError:
            raise ImportError('The langid module is needed for LanguageFilter '
                              'to work.')

    def transform(self, obj):
        text = '\n'.join(obj.get(field, '') for field in self.fields)
        return self.langid.classify(text)[0] in self.languages


class DomainFilter(Filter):
    def __init__(self, tlds, field='url', retain=True):
        """
        Filters all urls (by default) not in, or, if the retain argument
        is False, in the the specified TLDs.
        """
        super(DomainFilter, self).__init__()
        self.field = field
        self.tlds = set(tlds)
        self.check = self.__in if retain else self.__not_in

    def __in(self, tld):
        return tld in self.tlds

    def __not_in(self, tld):
        return tld not in self.tlds

    def transform(self, obj):
        return self.check(tldextract.extract(obj[self.field]).suffix.lower())
