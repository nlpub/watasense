#!/usr/bin/env python

import os
import sys
from flask import Flask, render_template, send_from_directory, url_for, redirect, request
from flask_misaka import Misaka
import mnogoznal

app = Flask(__name__)
Misaka(app)

if 'PYRO4_W2V' in os.environ:
    from mnogoznal.pyro_vectors import PyroVectors as PyroVectors
    w2v = PyroVectors(os.environ['PYRO4_W2V'])
elif 'W2V_PATH' in os.environ:
    from gensim.models import KeyedVectors
    w2v = KeyedVectors.load_word2vec_format(os.environ['W2V_PATH'], binary=True, unicode_errors='ignore')
    w2v.init_sims(replace=True)
else:
    print('No word2vec model is loaded. Please set the PYRO4_W2V or W2V_PATH environment variable.', file=sys.stderr)

# Загрузка базы данных из файла
#filename = 'D:\Documents\Study\Projects\Python\mnogoznal\watset-mcl-mcl-joint-exp-linked.tsv'
filename = 'watset-mcl-mcl-joint-exp-linked.tsv'
wsd_class = mnogoznal.SparseWSD(filename=filename)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/wsd')
def wsd_redirect():
    return redirect(url_for('.index'), code=302)


@app.route('/wsd', methods=['POST'])
def wsd():
    text_box_value = request.form["text"]
    spans = mnogoznal.mystem(text_box_value)
    result = wsd_class.disambiguate(spans)
    return render_template('wsd.html',
                           output=result,
                           synonyms=wsd_class.synonyms,
                           hyperonimuses=wsd_class.hypernyms)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()
