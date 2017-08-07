#!/usr/bin/env python

from flask import Flask, render_template, send_from_directory, url_for, redirect, request
from flask_misaka import Misaka
import mnogoznal
import os
import sys
app = Flask(__name__)
Misaka(app)

# Загрузка базы данных из файла
#filename = 'D:\Documents\Study\Projects\Python\mnogoznal\watset-mcl-mcl-joint-exp-linked.tsv'
filename = 'watset-mcl-mcl-joint-exp-linked.tsv'

if 'PYRO4_W2V' in os.environ:
    w2v_type = 'PYRO4_W2V'
    w2v_path = os.environ['PYRO4_W2V']
elif 'W2V_PATH' in os.environ:
    w2v_type = 'W2V_PATH'
    w2v_path = os.environ['W2V_PATH']
else:
    print('No word2vec model is loaded. Please set the PYRO4_W2V or W2V_PATH environment variable.',
          file=sys.stderr)
    exit()

# Создание классов для различных методов обработки
wsd_sparse = mnogoznal.SparseWSD(inventory_path=filename)
wsd_dense = mnogoznal.DenseWSD(inventory_path=filename, w2v_type=w2v_type, w2v_path=w2v_path)


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
    result = wsd_sparse.disambiguate(spans)
    return render_template('wsd.html',
                           output=result,
                           synonyms=wsd_sparse.synonyms,
                           hyperonimuses=wsd_sparse.hypernyms)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()
