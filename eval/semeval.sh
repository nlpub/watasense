#!/bin/bash -ex

export LANG=en_US.UTF-8 LC_COLLATE=C

for pos in nouns verbs; do
  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyBCubed \
    $pos.key \
    $pos-baseline-every.key |
  tee b3-$pos-baseline-every.txt

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyBCubed \
    $pos.key \
    $pos-baseline-one.key |
  tee b3-$pos-baseline-one.txt

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyBCubed \
    $pos.key \
    ../${pos}_test.key |
  tee b3-$pos-test.txt

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyNormalizedMutualInformation \
    $pos.key \
    $pos-baseline-every.key |
  tee nmi-$pos-baseline-every.txt

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyNormalizedMutualInformation \
    $pos.key \
    $pos-baseline-one.key |
  tee nmi-$pos-baseline-one.txt

  java -cp cluster-comparison-tools.jar \
    edu.ucla.clustercomparison.FuzzyNormalizedMutualInformation \
    $pos.key \
    ../${pos}_test.key |
  tee nmi-$pos-test.txt
done
