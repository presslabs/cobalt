# -*- coding: utf-8 -*-
# vim: ft=python:sw=4:ts=4:sts=4:et:
import json

from flask import Flask, Blueprint, Response, current_app

from volume import Volume, VolumeManager


volume = Blueprint('volume', __name__)

def create_api_server(volume_manager):
    app = Flask(__name__)
    app.volume_manager = volume_manager
    app.debug = True

    app.register_blueprint(volume, url_prefix='/volumes')

    return app

@volume.route('/', methods=['GET'])
def get_volumes():
    volumes = current_app.volume_manager
    return Response(
        '[' + ', '.join([v.to_json() for v in volumes]) + ']',
        content_type='application/json')
