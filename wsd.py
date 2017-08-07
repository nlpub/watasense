#!/usr/bin/env python

import argparse
import mnogoznal
import sys

parser = argparse.ArgumentParser(description='WSD.')
parser.add_argument('--inventory', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--mystem', required=True, type=argparse.FileType('rb'))
parser.add_argument('--mode', choices=('sparse', 'dense'), default='sparse', type=str)
parser.add_argument('--w2v', default=None, type=argparse.FileType('rb'))
args = parser.parse_args()

if args.mode == 'dense' and args.w2v is None:
    print('Please set the --w2v option to engage the dense mode.', file=sys.stderr)
    exit()

text = input()

if args.mode == 'sparse':
    wsd_class = mnogoznal.SparseWSD(inventory_path=args.inventory)
    mystem_text = mnogoznal.mystem(text)
    result = wsd_class.disambiguate(mystem_text)

elif args.mode == 'dense':
    wsd_class = mnogoznal.DenseWSD(inventory_path=args.inventory, w2v_type='W2V_PATH', w2v_path=args.w2v)
    mystem_text = mnogoznal.mystem(text)
    result = wsd_class.disambiguate(mystem_text)

for sentence in result:
    for word in sentence:
        print(word[0], '\t', word[2], '\t', word[1])
    print()