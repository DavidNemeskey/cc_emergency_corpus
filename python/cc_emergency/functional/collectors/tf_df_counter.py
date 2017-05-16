#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Counts the occurrences of tokens in the fields specified by the user, and
aggregates them both as (corpus) TF and DF.
"""
from future.utils import viewkeys
from collections import Counter


class TFDFCollector(Collector):
    def __init__(self, field_weights, tf_df_names=None):
        """
        The field_weights dictionary: {field: weight} specifies which fields to
        convert, and how much weight to give the tokens therein. This only
        affects the TF computation.

        tf_df_names is a tuple that sets the name of the TF and DF fields. The
        default, not surprisingly, is ("TF", "DF").
        """
        self.field_weights = field_weights
        self.tf_df_names = ("TF", "DF") if not tf_df_names else tf_df_names
        self.logger = logging.getLogger(
            self.__class__.__module__ + '.' + self.__class__.__name__)

    def __call__(self, it):
        df, tf = Counter(), Counter()
        for obj in it:
        dfs = set()
        for field, weight in self.field_weights.items():
            dfs |= obj[field
