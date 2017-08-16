#!/bin/bash -ex

export LANG=en_US.UTF-8 LC_COLLATE=C

INVENTORY="${INVENTORY:-../watset-mcl-mcl-joint-exp-linked.tsv}"

if [ -z ${W2V_PYRO+x} ]; then
  W2V_PATH="${W2V_PATH:-../../projlearn/all.norm-sz100-w10-cb0-it1-min100.w2v}"
  W2V=--w2v=$W2V_PATH
else
  W2V=--pyro=$W2V_PYRO
fi

CWD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

which mystem >/dev/null 2>&1 || (echo 'Please make sure that mystem is in PATH.' && exit 1)

for pos in nouns verbs; do
  $CWD/../tests.py --inventory=$INVENTORY --mystem=$(which mystem) --mode=sparse $pos.tsv >$pos-sparse.key
  $CWD/../tests.py --inventory=$INVENTORY --mystem=$(which mystem) --mode=dense $W2V $pos.tsv >$pos-dense.key

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
