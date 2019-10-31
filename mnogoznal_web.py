#!/usr/bin/env python3

import os
import sys

from flask import Flask, render_template, send_from_directory, url_for, redirect, request, jsonify
from flask_misaka import Misaka

import mnogoznal
import mnogoznal_web_assets

app = Flask(__name__)
Misaka(app)

mnogoznal_web_assets.init(app)

inventory = mnogoznal.Inventory(os.environ.get('INVENTORY', 'watset-cw-nolog-mcl-joint-exp-linked.tsv'))

WSD = {'sparse': mnogoznal.SparseWSD(inventory)}
WSD['lesk'] = mnogoznal.LeskWSD(inventory)

if 'W2V_PYRO' in os.environ:
    from mnogoznal.pyro_vectors import PyroVectors as PyroVectors

    w2v = PyroVectors(os.environ['W2V_PYRO'])
    WSD['dense'] = mnogoznal.DenseWSD(inventory, wv=w2v)
elif 'W2V_PATH' in os.environ:
    from gensim.models import KeyedVectors

    w2v = KeyedVectors.load_word2vec_format(os.environ['W2V_PATH'], binary=True, unicode_errors='ignore')
    w2v.init_sims(replace=True)
    WSD['dense'] = mnogoznal.DenseWSD(inventory, wv=w2v)
else:
    print('Please set the W2V_PYRO or W2V_PATH environment variable to enable the dense mode.', file=sys.stderr)


@app.route('/')
def index():
    return render_template('index.html', modes=WSD.keys())


@app.route('/wsd')
def wsd_redirect():
    return redirect(url_for('.index'), code=302)


@app.route('/wsd', methods=['POST'])
def wsd():
    mode = request.form.get('mode', 'dense' if 'dense' in WSD else 'sparse' or 'lesk')
    wsd = WSD[mode]

    sentences = mnogoznal.mystem(request.form['text'])
    results = [wsd.disambiguate(sentence) for sentence in sentences]

    return render_template('wsd.html', mode=mode, inventory=inventory, results=results)


@app.route('/wsd.json', methods=['POST'])
def wsd_json():
    mode = request.form.get('mode', 'dense' if 'dense' in WSD else 'sparse' or 'lesk')
    wsd = WSD[mode]

    sentences = mnogoznal.mystem(request.form['text'])
    results = [[(list(span), sid) for span, sid in wsd.disambiguate(sentence).items()] for sentence in sentences]

    return jsonify(results)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run()
