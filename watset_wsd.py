#!/usr/bin/env python

from flask import Flask, render_template, send_from_directory, url_for, redirect, request
from flask_misaka import Misaka
from flask_assets import Environment, Bundle
import mnogoznal
import os
import sys

app = Flask(__name__)
Misaka(app)

assets = Environment(app)
assets.url = app.static_url_path
assets.directory = app.static_folder
assets.append_path('assets/scss')

scss = Bundle('stylesheet.scss', filters='pyscss', output='stylesheet.css')
assets.register('scss_all', scss)

inventory = mnogoznal.Inventory(os.environ.get('INVENTORY', 'watset-mcl-mcl-joint-exp-linked.tsv'))

WSD = {'sparse': mnogoznal.SparseWSD(inventory)}

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
    mode   = request.form.get('mode', 'dense' if 'dense' in WSD else 'sparse')
    wsd    = WSD[mode]

    sentences = mnogoznal.mystem(request.form['text'])
    results = [wsd.disambiguate(sentence) for sentence in sentences]

    return render_template('wsd.html', mode=mode, inventory=inventory, results=results)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()
