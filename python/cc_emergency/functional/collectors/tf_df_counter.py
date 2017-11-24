#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Counts the occurrences of tokens in the fields specified by the user, and
aggregates them both as (corpus) TF and DF.
"""

from future.utils import viewkeys
from collections import Counter

from cc_emergency.functional.core import Collector
from cc_emergency.functional.io import JsonWriter


class TFDFCollector(Collector):
    def __init__(self, field_weights, tf_df_names=None, *args, **kwargs):
        """
        The field_weights dictionary: {field: weight} specifies which fields to
        convert, and how much weight to give the tokens therein. This only
        affects the TF computation.

        tf_df_names is a tuple that sets the name of the TF and DF fields. The
        default, not surprisingly, is ("TF", "DF").
        """
        super(TFDFCollector, self).__init__(*args, **kwargs)
        self.field_weights = field_weights
        self.tf_df_names = ("TF", "DF") if not tf_df_names else tf_df_names

    def __call__(self, it):
        counts = {field: dict(zip(self.tf_df_names, [Counter(), Counter()]))
                  for field in self.field_weights.keys()}
        for obj in it:
            for field, weight in self.field_weights.items():
                field_counts = obj[field + '_counts']
                counts[field][self.tf_df_names[0]].update(
                    {w: f * weight for w, f in field_counts.items()})
                counts[field][self.tf_df_names[1]].update(viewkeys(field_counts))
        return counts


class TFDFWriter(TFDFCollector, JsonWriter):
    """
    Same as TFDFCollector, only writes the dict from each file into file.
    This is needed because sometimes the output is too big to be serialized
    via the other class. I really need to fix how run_queued works...
    """
    def __init__(self, output_file, field_weights, tf_df_names=None):
        super(TFDFWriter, self).__init__(
            field_weights, tf_df_names, output_file)

    def __call__(self, it):
        counts = super(TFDFWriter, self).__call__(it)
        JsonWriter.__call__(self, [counts])
