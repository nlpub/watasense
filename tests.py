#!/usr/bin/env python

import argparse
import csv
import mnogoznal
import os
import sys

parser = argparse.ArgumentParser(description='WSD.')
parser.add_argument('--inventory', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--mystem', required=True, type=argparse.FileType('rb'))
parser.add_argument('--mode', choices=('sparse', 'dense'), default='sparse', type=str)
group = parser.add_mutually_exclusive_group()
group.add_argument('--w2v', default=None, type=argparse.FileType('rb'))
group.add_argument('--pyro', default=None, type=str)
parser.add_argument('instances', type=argparse.FileType('r', encoding='UTF-8'))
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

source_list = list()
text_string = str()

# Считывание данных из файла
reader = csv.reader(args.instances, delimiter='\t', quoting=csv.QUOTE_NONE)
for row in reader:
    source_list.append(row)
    if len(text_string) > 0:
        text_string = text_string + '\n\n\t\n\n'
    text_string = text_string + (row[2] + ' ' + row[3] + row[4]).replace('  ', ' ')

# Собираем все предложения в одну кучу
# И запихиваем в mystem (для экономии времени)
text_string = text_string + '\n\n\t'
text_mystem = mnogoznal.mystem(text_string)
text_mystem_list = list()
element_list = list()
for element in text_mystem:
    for subj in element:
        if subj[0] == '\\t':
            text_mystem_list.append(element_list)
            element_list = list()
        else:
            element_list.append(subj)

for i, (lemma, instance, _, word, _) in enumerate(source_list):
    (lemma, pos), word = lemma.split('.', 1), word.strip()

    index = [sword.strip() for sword, _, _ in text_mystem_list[i]].index(word)

    id = wsd.disambiguate_word(text_mystem_list[i], index)

    print(' '.join((
        '%s.%s' % (lemma, pos),
        instance,
        '%s.%s.%d' % (lemma, pos, id if id is not None else 0)
    )))

    print('%d instance(s) done.' % (i + 1), file=sys.stderr)
