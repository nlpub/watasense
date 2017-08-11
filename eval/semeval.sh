#!/bin/bash -ex

export LANG=en_US.UTF-8 LC_COLLATE=C

for pos in nouns verbs; do
  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyBCubed \
    $pos.key \
    $pos.key

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyNormalizedMutualInformation \
    $pos.key \
    $pos.key

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyRandIndex \
    $pos.key \
    $pos.key
done
