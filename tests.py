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
parser.add_argument('--w2v', default=None, type=argparse.FileType('rb'))
parser.add_argument('instances', type=argparse.FileType('r', encoding='UTF-8'))
args = parser.parse_args()

if args.mode == 'sparse':
    wsd = mnogoznal.SparseWSD(inventory_path=args.inventory.name)
elif args.mode == 'dense':
    if args.w2v is None:
        print('Please set the --w2v option to engage the dense mode.', file=sys.stderr)
        exit(1)

    wsd = mnogoznal.DenseWSD(inventory_path=args.inventory.name, w2v_type='gensim', w2v_path=args.w2v)

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

for i, row in enumerate(source_list):
    lemma, pos     = row[0].split('.', 1)
    instance, word = row[1], row[3].strip()

    spans = [text_mystem_list[i]]
    sid = wsd.disambiguate_word(spans, word)

    print('%s.%s' % (lemma, pos) + ' ' +
          instance + ' ' +
          '%s.%s.%d' % (lemma, pos, sid if isinstance(sid, int) else 0))
    print('%d instance(s) done.' % i, file=sys.stderr)
