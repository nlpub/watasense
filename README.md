# Mnogoznal

Mnogoznal is a system for word sense disambiguation (WSD). It includes three components:

* a Python library for WSD;
* a Web service for WSD;
* an evaluation framework.

## Python Library

TBA

## Web Service

1. `pip install -r requirements.txt`
2. `W2V_PATH=model.w2v ./watset_wsd.py`

Please note that the Web service container image is available on [Docker Hub](https://hub.docker.com/r/nlpub/mnogoznal/).

## Evaluation Framework

1. `cd eval`
2. `make gold instances baseline cluster-comparison-tools`
3. `./semeval.sh`

## Citation

TBA

## Copyright

This repository contains the implementation of Mnogoznal. See LICENSE for details.
