export LANG:=en_US.UTF-8
export LC_COLLATE:=C
export SHELL:=/bin/bash

watlink-dialogue2017.tar.xz:
	curl -sLO 'https://github.com/dustalov/watlink/releases/download/v1.0/watlink-dialogue2017.tar.xz'

watlink: watlink-dialogue2017.tar.xz
	tar Jxvf watlink-dialogue2017.tar.xz watlink-dialogue2017/eval/ru/tfidf/watset-mcl-mcl-joint-exp-linked.tsv --strip=4

rwn.xml:
	@echo "# Assuming that you have RuWordNet in the directory ${CURDIR}/rwn-xml."
	./ruthes-stub.awk -v TAG=rwn rwn-xml/*.*.xml >rwn.xml || echo "No RuWordNet for you." >/dev/stderr

rwn: rwn.xml
	xsltproc rwn-linked.xsl rwn.xml | ./rwn-linked.awk >rwn-linked.tsv || echo "No RuWordNet for you." >/dev/stderr

clean:
	rm -fv rwn.xml rwn-linked.tsv
	rm -fv watlink-dialogue2017.tar.xz watset-mcl-mcl-joint-exp-linked.tsv
