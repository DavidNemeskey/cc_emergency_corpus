#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Duplicate detection, with LSH. The second part of the process, the first of
which is implemented in transforms/minhash.
"""

from __future__ import absolute_import, division, print_function
import base64
import pickle

from cc_emergency.functional.core import Collector

from datasketch import MinHashLSH


class LSH(Collector):
    def __init__(self, id_field, threshold, num_perm=128, return_obj=False):
        """
        Locality-sensitive hashing that keeps a single document from all
        clusters and outputs the list of unique urls. Parameters:
        - id_field the id field in the document
        - threshold the LSH (Jaccard) similarity threshold
        - num_perm the number of permutations in minhash
        - return_obj if True, the whole objects are collected into the lists;
                     otherwise, only their id fields (the default).
        """
        super(LSH, self).__init__()
        self.id_field = id_field
        self.threshold = threshold
        self.num_perm = num_perm
        self.return_obj = return_obj

    def __call__(self, it):
        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        ids = []  # The ids / objects to return
        for obj in it:
            mh = pickle.loads(
                base64.b85decode(obj['minhash'].encode('us-ascii')))
            result = lsh.query(mh)
            if not result:
                try:
                    lsh.insert(obj[self.id_field], mh)
                    ids.append(obj if self.return_obj else obj[self.id_field])
                except ValueError as ve:
                    self.logger.debug('Error adding id: {} to LSH ({})'.format(
                        obj[self.id_field], ve.args[0]))
        return ids
