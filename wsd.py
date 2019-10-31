#!/usr/bin/env python3

import argparse
import concurrent.futures
import sys

import mnogoznal

parser = argparse.ArgumentParser(description='WSD.')
parser.add_argument('--inventory', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--mystem', required=True, type=argparse.FileType('rb'))
parser.add_argument('--mode', choices=('sparse', 'dense'), default='sparse', type=str)
group = parser.add_mutually_exclusive_group()
group.add_argument('--w2v', default=None, type=argparse.FileType('rb'))
group.add_argument('--pyro', default=None, type=str)
args = parser.parse_args()

inventory = mnogoznal.Inventory(inventory_path=args.inventory.name)

if args.mode == 'sparse':
    wsd = mnogoznal.SparseWSD(inventory=inventory)
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

    wsd = mnogoznal.DenseWSD(inventory=inventory, wv=w2v)

sentences = mnogoznal.mystem(input())


def disambiguate(index):
    return wsd.disambiguate(sentences[index])


with concurrent.futures.ProcessPoolExecutor() as executor:
    for i, result in enumerate(executor.map(disambiguate, range(len(sentences)))):
        for (word, lemma, pos, _), id in result.items():
            print('\t'.join((word, lemma, pos, id if id is not None else '')))

        if i + 1 < len(sentences):
            print()
