export LANG:=en_US.UTF-8
export LC_COLLATE:=C

pip:
	pip install -r requirements.txt

gold:
	./rlwsd2semeval.py --pos=nouns >nouns.key
	./rlwsd2semeval.py --pos=verbs >verbs.key

baseline:
	awk '{print $$1, $$2, $$1 ".1"}'   nouns.key >nouns-one.key
	awk '{print $$1, $$2, $$1 ".1"}'   verbs.key >verbs-one.key
	awk '{print $$1, $$2, $$1 "." NR}' nouns.key >nouns-spi.key
	awk '{print $$1, $$2, $$1 "." NR}' verbs.key >verbs-spi.key

instances:
	./rlwsd2semeval.py --pos=nouns --mode=instances >nouns.tsv
	./rlwsd2semeval.py --pos=verbs --mode=instances >verbs.tsv

clean:
	rm -fv *.key ari-*.txt vm-*.txt {nouns,verbs}.tsv
