#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Counts the occurrences of tokens in the fields specified by the user, and
aggregates them both as (corpus) TF and DF.
"""

from future.utils import viewkeys
from collections import Counter

from cc_emergency.functional.core import Collector


class TFDFCollector(Collector):
    def __init__(self, field_weights):
        """
        The field_weights dictionary: {field: weight} specifies which fields to
        convert, and how much weight to give the tokens therein. This only
        affects the TF computation.
        """
        self.field_weights = field_weights

    def __call__(self, it):
        tf, df = Counter(), Counter()
        for obj in it:
            dfs = set()
            for field, weight in self.field_weights.items():
                dfs |= viewkeys(obj[field])
                tf.update({w: f * weight for w, f in obj[field].items()})
            df.update(dfs)
        return tf, df
