#!/usr/bin/env python

import argparse
import os
import rl_wsd_labeled

POS = {
    'nouns': 'n',
    'verbs': 'v'
}

parser = argparse.ArgumentParser(description='Labeled Russian Context for WSD to SemEval 2013 Task 13.')
parser.add_argument('--pos', required=True, choices=POS.keys())
args = parser.parse_args()

def contexts(pos, corpus='RuTenTen'):
    path = os.path.dirname(rl_wsd_labeled.contexts_filename(pos, corpus, 'word'))
    words = [word[:-4] for word in os.listdir(path) if word.endswith('.txt')]
    return [(word, rl_wsd_labeled.get_contexts(rl_wsd_labeled.contexts_filename(pos, corpus, word))) for word in sorted(words)]

for word, (senses, instances) in contexts(args.pos):
    lexelt = '.'.join((word, POS[args.pos]))

    for i, (_, sid) in enumerate(instances):
        instance = '.instance.'.join((lexelt, str(i)))
        sense = '.'.join((lexelt, sid))

        # lemma.partOfSpeech instance-id sense-name/applicability-rating
        print(' '.join((lexelt, instance, sense)))
