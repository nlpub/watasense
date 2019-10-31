#!/usr/bin/env python3

from os import path

from flask import Flask
from flask_assets import Bundle, Environment


def init(app=None):
    app = app or Flask(__name__)

    with app.app_context():
        env = Environment(app)
        env.load_path = [path.join(path.dirname(__file__), 'assets')]
        env.url = app.static_url_path
        env.directory = app.static_folder
        env.auto_build = app.debug
        env.manifest = 'file'

        scss = Bundle('stylesheet.scss', filters='pyscss', output='stylesheet.css')
        env.register('scss_all', scss)

        bundles = [scss]
        return bundles


if __name__ == '__main__':
    bundles = init()

    for bundle in bundles:
        bundle.build()
