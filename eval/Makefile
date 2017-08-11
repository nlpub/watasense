export LANG:=en_US.UTF-8
export LC_COLLATE:=C

CCT:=https://storage.googleapis.com/google-code-archive-source/v2/code.google.com/cluster-comparison-tools/source-archive.zip

pip:
	pip install -r requirements.txt

gold:
	./rlwsd2semeval.py --pos=nouns >nouns.key
	./rlwsd2semeval.py --pos=verbs >verbs.key

instances:
	./rlwsd2semeval.py --pos=nouns --mode=instances >nouns.tsv
	./rlwsd2semeval.py --pos=verbs --mode=instances >verbs.tsv

cluster-comparison-tools.jar:
	rm -rf 'cluster-comparison-tools'
	curl -sL '$(CCT)' -o 'cluster-comparison-tools.zip' && unzip 'cluster-comparison-tools.zip'
	cd cluster-comparison-tools/trunk && mvn -T $$(nproc) package
	mv -fv cluster-comparison-tools/trunk/target/cluster-comparison-tools-1.0.0-jar-with-dependencies.jar cluster-comparison-tools.jar

clean:
	rm -fv nouns.key verbs.key nouns.tsv verbs.tsv
	rm -rf cluster-comparison-tools cluster-comparison-tools.jar cluster-comparison-tools.zip
