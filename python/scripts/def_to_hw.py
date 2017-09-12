#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Returns the list of headwords whose definition contain the input words."""

from argparse import ArgumentParser
from collections import defaultdict


def parse_arguments():
    parser = ArgumentParser(
        description='Returns the list of headwords whose definition contain '
                    'the input words.')
    parser.add_argument('input_file', help='a word list file.')
    parser.add_argument('--dictionary', '-d', required=True,
                        help='the dictionary file.')
    return parser.parse_args()


def index_dict(dict_file):
    index = defaultdict(set)
    with open(dict_file) as inf:
        for line in inf:
            hw, defs, *_ = line.strip().split('\t')
            for word in defs.split():
                index[word].add(hw)
    return index


def query(words, index):
    found = defaultdict(set)
    for word in words:
        for hw in index.get(word, {}):
            found[hw].add(word)
    return found


def main():
    args = parse_arguments()

    index = index_dict(args.dictionary)
    with open(args.input_file) as inf:
        word_list = sorted(l.strip() for l in inf)

    found = query(word_list, index)
    for hw, words in sorted(found.items()):
        print('{}\t{}'.format(hw, ', '.join(sorted(words))))


if __name__ == '__main__':
    main()
