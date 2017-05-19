#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Duplicate detection, slowly. A faster implementation would first transform the
document -> shingles mapping to shingle -> documents, run the minhash there
(once for every shingle), and then merge them again to get the document
signatures. If this turns out very slow, I might attempt that...
"""

from __future__ import absolute_import, division, print_function
import base64
from builtins import range
import pickle

from cc_emergency.functional.core import Map

from datasketch import MinHash as MeanHash
from datasketch import LeanMinHash as LeanMeanHash

class MinHash(Map):
    """The map part of the duplicate detection process."""
    def __init__(self, fields, shingles=5, num_perm=128):
        """
        Parameters:
        - fields: the fields to "shinglize". Each field must be a sequence of
                  items, e.g. a list of words or a string (of characters)
        - shingles: the N in N-shingles (-grams)
        - num_perm: the number of permutations for minhash.
        """
        super(MinHash, self).__init__()
        self.fields = fields
        self.shingles = shingles
        self.num_perm = num_perm

    def transform(self, obj):
        shingles = set()
        for field in filter(lambda f: f in obj and obj[f], self.fields):
            shingles |= set(self.shinglize(obj[field]))
        if shingles:
            m = MeanHash(num_perm=self.num_perm)
            for sh in shingles:
                m.update(' '.join(sh).encode('utf-8'))
            obj['minhash'] = base64.b85encode(
                pickle.dumps(LeanMeanHash(m))).decode('us-ascii')
            return obj

    def shinglize(self, seq):
        """N-shinglize the sequence."""
        for i in range(len(seq) - self.shingles + 1):
            yield tuple(seq[i:i + self.shingles])
