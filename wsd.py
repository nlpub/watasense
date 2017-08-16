#!/usr/bin/env python

import argparse
import mnogoznal
from mnogoznal.wsd import SparseWSD as NewSparseWSD
from mnogoznal.wsd import DenseWSD as NewDenseWSD
import sys

parser = argparse.ArgumentParser(description='WSD.')
parser.add_argument('--inventory', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--mystem', required=True, type=argparse.FileType('rb'))
parser.add_argument('--mode', choices=('sparse', 'dense'), default='sparse', type=str)
group = parser.add_mutually_exclusive_group()
group.add_argument('--w2v', default=None, type=argparse.FileType('rb'))
group.add_argument('--pyro', default=None, type=str)
args = parser.parse_args()

if args.mode == 'sparse':
    wsd = mnogoznal.SparseWSD(inventory_path=args.inventory.name)
elif args.mode == 'dense':
    if args.w2v:
        from gensim.models import KeyedVectors
        w2v = KeyedVectors.load_word2vec_format(args.w2v, binary=True, unicode_errors='ignore')
        w2v.init_sims(replace=True)
    elif args.pyro:
        from mnogoznal.pyro_vectors import PyroVectors as PyroVectors
        w2v = PyroVectors(args.pyro)
    else:
        print('Please set the --w2v or --pyro option to engage the dense mode.', file=sys.stderr)
        exit(1)

    wsd = mnogoznal.DenseWSD(inventory_path=args.inventory.name, wv=w2v)

spans = mnogoznal.mystem(input())

result = wsd.disambiguate(spans)

for i, sentence in enumerate(result):
    for (word, lemma, pos), id in sentence.items():
        print('\t'.join((word, lemma, pos, str(id) if id is not None else '')))

    if i + 1 < len(result):
        print()
