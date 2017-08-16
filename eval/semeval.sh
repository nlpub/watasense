#!/bin/bash -ex

export LANG=en_US.UTF-8 LC_COLLATE=C

INVENTORY=../watset-mcl-mcl-joint-exp-linked.tsv
W2V=../../projlearn/all.norm-sz100-w10-cb0-it1-min100.w2v

CWD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

which mystem >/dev/null 2>&1 || (echo 'Please make sure that mystem is in PATH.' && exit 1)

for pos in nouns verbs; do
  $CWD/../tests.py --inventory=$INVENTORY --mystem=$(which mystem) --mode=sparse $pos.tsv >$pos-sparse.key
  $CWD/../tests.py --inventory=$INVENTORY --mystem=$(which mystem) --mode=dense --w2v=$W2V $pos.tsv >$pos-dense.key

  for method in one spi sparse dense; do
    java -cp cluster-comparison-tools.jar \
      edu.ucla.clustercomparison.FuzzyBCubed \
      $pos.key $pos-$method.key | tee b3-$pos-$method.txt

    java -cp cluster-comparison-tools.jar \
      edu.ucla.clustercomparison.FuzzyNormalizedMutualInformation \
      $pos.key $pos-$method.key | tee nmi-$pos-$method.txt

    files="$files $pos-$method.key"
  done

  ./vmeasure.py --gold=$pos.key $files | tee vm-$pos.tsv

  unset files
done
