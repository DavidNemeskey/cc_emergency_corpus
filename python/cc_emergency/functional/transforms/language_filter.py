#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Language / domain filtering transforms."""

from functools import partial
import importlib
import inspect

import tldextract

from cc_emergency.functional.core import Filter
from cc_emergency.utils import first


class LanguageFilter(Filter):
    """Filters objects for language(s)."""
    LIBRARIES = {'langid': 'langid', 'cld2': 'cld2-cffi'}

    def __init__(self, fields, languages, libraries=None):
        """
        - fields: either the name of the field on which to perform the language
                  identification, or a list of fields
        - languages: either the name of a language or a list of languages
        - libraries: the libraries to try, in order. The default is cld2 alone,
                     but langid is also supported, as well as any combinations
                     of these two.
        """
        super(LanguageFilter, self).__init__()
        if not isinstance(fields, list):
            fields = [fields]
        if not isinstance(languages, list):
            languages = [languages]
        self.languages = set(languages)
        self.fields = fields
        self.libraries = libraries if libraries else ['cld2']
        self.detectors = []

    def __enter__(self):
        if self.lib not in self.LIBRARIES:
            raise ValueError('Unsupported library "{}"'.format(self.lib))
        try:
            for lib in self.libraries:
                self.logger.debug('Loading {}...'.format(lib))
                detector_lib = importlib.import_module(lib)
                detector_fn = inspect.getmembers(
                    self,
                    lambda o: inspect.ismethod(o) and o.__name__ == '__' + lib,
                )[0][1]
                self.detectors.append(partial(detector_fn, detector_lib))
            return self
        except ImportError:
            raise ImportError(
                'The {} module '.format(self.LIBRARIES[self.lib]) +
                'is needed for LanguageFilter to work.')

    def transform(self, obj):
        text = '\n'.join(obj.get(field, '') for field in self.fields)
        for detector in self.detectors:
            try:
                lang = detector(text)
                if lang != 'un':
                    return lang in self.languages
            except:
                pass
        else:
            self.logger.debug(
                'Could not detect language for document {}'.format(
                    first(obj.values())))
            return False

    def __langid(self, lib, text):
        return lib.classify(text)[0]

    def __cld2(self, lib, text):
        return lib.detect(text).details[0].language_code


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
