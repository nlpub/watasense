#!/usr/bin/env python

import argparse
import csv
from collections import defaultdict, OrderedDict
from concurrent.futures import ProcessPoolExecutor
from sklearn.metrics import homogeneity_score, completeness_score, v_measure_score
from sklearn.metrics import adjusted_rand_score

parser = argparse.ArgumentParser(description='SemEval 2010 WSI&D Task V-Measure')
parser.add_argument('--gold', required=True)
parser.add_argument('--measure', choices=('vmeasure', 'ari'), default='vmeasure', type=str)
parser.add_argument('path', nargs='+')
args = parser.parse_args()

def parse(filename):
    dataset = defaultdict(dict)

    with open(filename, 'r', encoding='UTF-8') as f:
        reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)

        for lemma, instance, sense in reader:
            dataset[lemma][instance] = sense

    return dataset

with ProcessPoolExecutor() as executor:
    paths   = args.path + [args.gold]
    systems = {path: wsd for path, wsd in zip(paths, executor.map(parse, paths))}

gold   = systems.pop(args.gold)
lemmas = sorted(gold.keys())
total  = sum(len(values) for values in gold.values())

def evaluate(path):
    system = systems[path]

    measure, scores, clusters_gold, clusters_system = 0., OrderedDict(), [], []

    for lemma in lemmas:
        instances = sorted(gold[lemma].keys())

        senses_gold   = {sid: i for i, sid in enumerate(sorted(set(gold[lemma].values())))}
        senses_system = {sid: i for i, sid in enumerate(sorted(set(system[lemma].values())))}

        clusters_gold   = [senses_gold[gold[lemma][instance]]     for instance in instances]
        clusters_system = [senses_system[system[lemma][instance]] for instance in instances]

        if 'vmeasure' == args.measure:
            measure += v_measure_score(clusters_gold, clusters_system) * len(instances) / total

            scores[lemma] = (
                homogeneity_score(clusters_gold, clusters_system),
                completeness_score(clusters_gold, clusters_system),
                v_measure_score(clusters_gold, clusters_system)
            )
        else:
            scores[lemma] = adjusted_rand_score(clusters_gold, clusters_system)

            measure += scores[lemma] * len(instances) / total

    return measure, scores

with ProcessPoolExecutor() as executor:
    results = {path: result for path, result in zip(systems, executor.map(evaluate, systems))}

if 'vmeasure' == args.measure:
    print('\t'.join(('path', 'lemma', 'homogeneity', 'completeness', 'vmeasure')))

    for path, (v_measure, scores) in results.items():
        print('\t'.join((path, '', '', '', '%.6f' % v_measure)))

        for lemma, (homogeneity, completeness, v_measure) in scores.items():
            print('\t'.join((
                path,
                lemma,
                '%.6f' % homogeneity,
                '%.6f' % completeness,
                '%.6f' % v_measure
            )))
else:
    print('\t'.join(('path', 'lemma', 'ari')))

    for path, (ari, scores) in results.items():
        print('\t'.join((path, '', '%.6f' % ari)))

        for lemma, ari in scores.items():
            print('\t'.join((path, lemma, '%.6f' % ari)))
