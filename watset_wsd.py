#!/usr/bin/env python

import os
from flask import Flask, render_template, send_from_directory, url_for, redirect, request
from flask_misaka import Misaka
from wsd.models import RequestWSD
from wsd import synsets

app = Flask(__name__)
Misaka(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wsd')
def wsd_redirect():
    return redirect(url_for('.index'), code=302)

@app.route('/wsd', methods=['POST'])
def wsd():
    text_box_value = request.form["input-text-name"]
    result = RequestWSD.wsd_func(text_box_value)
    return render_template('wsd.html', output=result, synsets=synsets)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()
