#!/usr/bin/env python

import argparse
import os
import sys

import rl_wsd_labeled

POS = {
    'nouns': 'n',
    'adjectives': 'a',
    'verbs': 'v'
}

parser = argparse.ArgumentParser(description='Labeled Russian Context for WSD to SemEval 2013 Task 13.')
parser.add_argument('--pos', required=True, choices=POS.keys())
parser.add_argument('--mode', choices=('gold', 'instances'), default='gold')
args = parser.parse_args()


def contexts(pos, corpus='RuTenTen'):
    path = os.path.dirname(rl_wsd_labeled.contexts_filename(pos, corpus, 'word'))

    for file in sorted(os.listdir(path)):
        word, ext = file.rsplit('.', 1)

        if not ext.lower() in ('txt', 'json'):
            continue

        yield word, rl_wsd_labeled.get_contexts(os.path.join(path, file))


total = 0

for i, (word, (senses, instances)) in enumerate(contexts(args.pos)):
    lexelt = '.'.join((word, POS[args.pos]))

    for j, ((left, token, right), sid) in enumerate(instances):
        instance = '.instance.'.join((lexelt, str(j)))

        if 'gold' == args.mode:
            # lemma.partOfSpeech instance-id sense-name/applicability-rating
            sense = '.'.join((lexelt, sid))
            print(' '.join((lexelt, instance, sense)))
        else:
            # lemma.partOfSpeech instance-id sentence
            print('\t'.join((lexelt, instance, left, token, right)))

    total += j + 1

print('The total number of examples for %s is %d for %d words.' % (args.pos, total, i + 1), file=sys.stderr)
