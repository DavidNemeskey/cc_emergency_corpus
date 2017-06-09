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
    def __init__(self, domains, field='url', expression='suffix', retain=True):
        """
        Filters all urls (by default) not in, or, if the retain argument
        is False, in the the specified list. The class allows the user to
        assemble an expression from the parts of a domain (subdomain,
        domain and suffix), and the class will compare that agains the list.
        The default expression is 'suffix', i.e. the TLD.
        """
        super(DomainFilter, self).__init__()
        self.field = field
        self.domains = set(domains)
        self.expression = compile(expression, '<string>', 'eval')
        self.check = self.__in if retain else self.__not_in

    def __in(self, domain):
        return domain in self.domains

    def __not_in(self, domain):
        return domain not in self.domains

    def transform(self, obj):
        variables = tldextract.extract(obj[self.field].lower())._asdict()
        return self.check(eval(self.expression, variables))
