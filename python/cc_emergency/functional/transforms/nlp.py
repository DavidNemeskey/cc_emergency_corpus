#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""NLP-related transformations."""

import nltk

from cc_emergency.functional.core import Map


class FilterStopwords(Map):
    def __init__(self, fields, language='english'):
        super(FilterStopwords, self).__init__()
        self.fields = fields
        self.language = language

    def __enter__(self):
        self.s = nltk.corpus.stopwords.words(self.language)

    def transform(self, obj):
        for field in self.fields:
            if field in obj:
                obj[field] = [w for w in obj[field] if w not in self.s]
        return obj
