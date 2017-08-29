#!/bin/bash -e

export LANG=en_US.UTF-8 LC_COLLATE=C

cat <<EOF
This script reproduces the results presented on the SIBIRCON 2017 conference.
EOF

echo
set -x

AVERAGE="${AVERAGE:-instances}"

make gold instances baseline

for pos in nouns adjectives verbs; do
  for method in one spi; do
    files="$files $pos-$method.key"
  done

  ./measure.py --measure=vmeasure --average=$AVERAGE --gold=$pos.key $files | tee vm-baseline-$pos.tsv

  ./measure.py --measure=ari      --average=$AVERAGE --gold=$pos.key $files | tee ari-baseline-$pos.tsv

  unset files
done

export W2V_PYRO=PYRO:w2v@localhost:9090
# export W2V_PATH=all.norm-sz100-w10-cb0-it1-min100.w2v

INVENTORY=../data/watset-cw-nolog-mcl-joint-exp-linked.tsv PREFIX=watlink- ./semeval.sh

INVENTORY=../data/ruthes-linked.tsv PREFIX=ruthes- ./semeval.sh

INVENTORY=../data/rwn-linked.tsv PREFIX=rwn- ./semeval.sh
