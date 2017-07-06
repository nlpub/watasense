#!/usr/bin/env python

from flask import Flask, render_template, url_for, redirect, request
from flask_misaka import Misaka
from wsd.models import RequestWSD

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
    return render_template('wsd.html', output=result)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run()
