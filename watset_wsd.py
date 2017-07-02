#!/usr/bin/env python

from flask import Flask, render_template, url_for, redirect
from flask_misaka import Misaka

app = Flask(__name__)
Misaka(app)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/wsd', methods=['GET'])
def wsd_redirect():
    return redirect(url_for('.index'), code=302)

@app.route('/wsd', methods=['POST'])
def wsd():
    return render_template('wsd.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run()
