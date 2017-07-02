#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Language / domain filtering transforms."""

import importlib
import inspect

import tldextract

from cc_emergency.functional.core import Filter


class LanguageFilter(Filter):
    """Filters objects for language(s)."""
    LIBRARIES = {'langid': 'langid', 'cld2': 'cld2-cffi'}

    def __init__(self, fields, languages, library='cld2'):
        """
        - fields: either the name of the field on which to perform the language
                  identification, or a list of fields
        - languages: either the name of a language or a list of languages
        - library: the library to use (langid or cld2).

        I know, the libraries should be enclosed in subclasses. C'est la vie.
        """
        super(LanguageFilter, self).__init__()
        if not isinstance(fields, list):
            fields = [fields]
        if not isinstance(languages, list):
            languages = [languages]
        self.languages = set(languages)
        self.fields = fields
        self.lib = library

    def __enter__(self):
        if self.lib not in self.LIBRARIES:
            raise ValueError('Unsupported library "{}"'.format(self.lib))
        try:
            self.logger.debug('Loading {}...'.format(self.lib))
            self.detector = importlib.import_module(self.lib)
            self.detect = inspect.getmembers(
                self,
                lambda o: inspect.ismethod(o) and o.__name__ == '__' + self.lib,
            )[0][1]
            return self
        except ImportError:
            raise ImportError(
                'The {} module '.format(self.LIBRARIES[self.lib]) +
                'is needed for LanguageFilter to work.')

    def transform(self, obj):
        text = '\n'.join(obj.get(field, '') for field in self.fields)
        return self.detect(text) in self.languages

    def __langid(self, text):
        return self.detector.classify(text)[0]

    def __cld2(self, text):
        return self.detector.detect(text).details[0].language_code


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
