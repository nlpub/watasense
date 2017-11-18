# Mnogoznal

Mnogoznal is a framework for unsupervised word sense disambiguation (WSD). It includes three components:

* a Python library for WSD;
* a Web service for WSD;
* an evaluation framework.

[![Dependency Status][gemnasium_badge]][gemnasium_link] [![Docker Hub][docker_badge]][docker_link]

[gemnasium_badge]: https://gemnasium.com/nlpub/mnogoznal.svg
[gemnasium_link]: https://gemnasium.com/nlpub/mnogoznal
[docker_badge]: https://img.shields.io/docker/pulls/nlpub/mnogoznal.svg
[docker_link]: https://hub.docker.com/r/nlpub/mnogoznal/

## Features

Mnogoznal implements two unsupervised WSD approaches:

* **sparse**: a vector space model approach that relies on cosine similarity;
* **dense**: a sense embeddings approach that based on [SenseGram](https://github.com/tudarmstadt-lt/sensegram).

Currently, Mnogoznal supports only the Russian language and the [Mystem](https://nlpub.ru/Mystem) tagger. Contributions are warmly welcome!

## Python Library

The sparse approach is the simplest.

```python
from mnogoznal import Inventory, SparseWSD, mystem

inventory = Inventory('….tsv')
wsd = SparseWSD(inventory)

sentences = mystem('Статья содержит описание экспериментов.')

for sentence in sentences:
    for (word, lemma, pos, _), id in wsd.disambiguate(sentence).items():
        print((word, lemma, pos, id))
```
```
('Статья', 'статья', 'S', '12641')
('содержит', 'содержать', 'V', '3240')
('описание', 'описание', 'S', '24626')
('экспериментов', 'эксперимент', 'S', '36055')
('.', '.', 'UNKNOWN', None)
```

To use the dense approach, it is necessary to load the word vectors using Gensim. The rest of the code is identical.

```python
from gensim.models import KeyedVectors
wv = KeyedVectors.load_word2vec_format('….w2v', binary=True, unicode_errors='ignore')
wv.init_sims(replace=True)

wsd = DenseWSD(inventory, wv)
```

It is also possible and highly convenient to use the remote word vectors served by [word2vec-pyro4](https://github.com/nlpub/word2vec-pyro4) instead of the Gensim ones.

```python
from mnogoznal.pyro_vectors import PyroVectors as PyroVectors
wv = PyroVectors('PYRO:w2v@…:9090')

wsd = DenseWSD(inventory, wv)
```

## Web Service

`INVENTORY=….tsv W2V_PATH=….w2v FLASK_APP=mnogoznal_web.py flask run` or `INVENTORY=….tsv W2V_PYRO=PYRO:w2v@…:9090 FLASK_APP=mnogoznal_web.py flask run`

Also, it is possible to run the Web service directly from [Docker Hub](https://hub.docker.com/r/nlpub/mnogoznal/):

```bash
docker run --rm -p 5000:5000 -e INVENTORY=….tsv -v ….tsv:/usr/src/app/….tsv:ro
```

## Evaluation Framework

1. `make -C data watlink`
2. `make -C eval gold instances baseline`
3. `cd eval && INVENTORY=….tsv W2V_PYRO=PYRO:w2v@…:9090 ./semeval.sh`

## Citation

* [Ustalov, D.](https://github.com/dustalov), [Teslenko, D.](https://github.com/pushkinue), [Panchenko, A.](https://github.com/alexanderpanchenko), [Chernoskutov, M.](https://github.com/chernoskutov): [Mnogoznal: an Unsupervised System for Word Sense Disambiguation](https://doi.org/10.1109/SIBIRCON.2017.8109857). In: Proceedings of the 2017 International Multi-Conference on Engineering, Computer and Information Sciences (SIBIRCON), Novosibirsk, Russia, IEEE (2017) 147–150

```bibtex
@inproceedings{Ustalov:17:sibircon,
  author    = {Ustalov, D. and Teslenko, D. and Panchenko, A. and Chernoskutov, M.},
  title     = {{Mnogoznal: an Unsupervised System for Word Sense Disambiguation}},
  booktitle = {2017 International Multi-Conference on Engineering, Computer and Information Sciences (SIBIRCON)},
  year      = {2017},
  pages     = {147--150},
  isbn      = {978-1-5386-1595-9},
  address   = {Novosibirsk, Russia},
  publisher = {IEEE},
  doi       = {10.1109/SIBIRCON.2017.8109857},
  language  = {english},
}
```

## Copyright

This repository contains the implementation of Mnogoznal. See LICENSE for details.
