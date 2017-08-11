CCT:=https://storage.googleapis.com/google-code-archive-source/v2/code.google.com/cluster-comparison-tools/source-archive.zip

gold:
	./rlwsd2semeval.py --pos=nouns >nouns.key
	./rlwsd2semeval.py --pos=verbs >verbs.key

instances:
	./rlwsd2semeval.py --pos=nouns --mode=instances >nouns.tsv
	./rlwsd2semeval.py --pos=verbs --mode=instances >verbs.tsv

cluster-comparison-tools.jar:
	rm -rf 'cluster-comparison-tools'
	curl -sLO '$(CCT)' && unzip 'source-archive.zip' && rm -fv 'source-archive.zip'
	cd cluster-comparison-tools/trunk && mvn -T $$(nproc) package
	mv -fv cluster-comparison-tools/trunk/target/cluster-comparison-tools-1.0.0-jar-with-dependencies.jar cluster-comparison-tools.jar
