#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""Converts CoNLL-format field(s) to text."""

from __future__ import absolute_import, division, print_function
from collections import Counter

from cc_emergency.functional.core import Map


class ConvertCoNLL(Map):
    """
    Converts CoNLL-format field(s) to text. Each sentence is mapped to a list
    of tokens.

    This class is "abstract"; users should instantiate on of the subclasses
    that implement the various output formats.

    TODO: convert to an ABC.
    """
    WORD, LEMMA, POS = range(3)

    def __init__(self, fields_columns):
        """
        The fields_columns dictionary:
        {field: [column, lower, convert_nnps, delete, new_field]}
        specifies which fields to convert, and then which column to use as the
        token. The column can be a number, or the words "word" (0) and
        "lemma" (1). lower indicates whether the token should be lowercased,
        while new_field is the name of the field where the result is put.

        If convert_nnps is specified, all NNP tokens are replaced by its value.
        """
        super(ConvertCoNLL, self).__init__()
        self.fields_columns = {
            field: [self.__column(spec[0])] + spec[1:]
            for field, spec in fields_columns.items()
        }

    def transform(self, obj):
        for field, spec in self.fields_columns.items():
            column, lower, convert_nnps, delete, new_field = spec
            if field in obj:
                tokens = [[self.__convert(token, column, lower, convert_nnps)
                           for token in sentence] for sentence in obj[field]]
                obj[new_field] = self.format(tokens)
                if delete:
                    del obj[field]
        return obj

    def format(self, tokens):
        """Formats the token lists."""
        raise NotImplementedError(
            'format is not implemented; use one of the subclasses.')

    def __convert(self, token, column, lower, convert_nnps):
        ret = token[column]
        if lower:
            ret = ret.lower()
        if convert_nnps and token[ConvertCoNLL.POS].startswith('NNP'):
            ret = convert_nnps
        return ret

    @staticmethod
    def __column(column):
        if isinstance(column, int):
            return column
        elif column.lower() == "word":
            return ConvertCoNLL.WORD
        elif column.lower() == "lemma":
            return ConvertCoNLL.LEMMA
        else:
            raise ValueError('Invalid column specifier "{}"'.format(column))


class CoNLLToCounts(ConvertCoNLL):
    """Collects all tokens into a Counter."""
    def format(self, tokens):
        return Counter([w for s in tokens for w in s])


class CoNLLToList(ConvertCoNLL):
    """Collects all tokens into a list."""
    def format(self, tokens):
        return [w for s in tokens for w in s]


class CoNLLToLists(ConvertCoNLL):
    """
    Formats a fields as a list of sentence token lists. If CoNLL field were
    NumPy arrays, this would be equivalent to [:,:,column].
    """
    def format(self, tokens):
        return tokens


class CoNLLToSet(ConvertCoNLL):
    """Collects all tokens into a set."""
    def format(self, tokens):
        return set([w for s in tokens for w in s])


class CoNLLToText(ConvertCoNLL):
    """Converts the field to SRILM-type text (one sentence each line)."""
    def format(self, tokens):
        return '\n'.join(' '.join(s) for s in tokens)
