from flask import Flask
from flask_restful import Api as RestApi

from api.volume import Volume, VolumeList

app = Flask(__name__)
api = RestApi(app)

app.debug = True
app.config['RESTFUL_JSON'] = {
    'separators': (', ', ': '),
    'indent': 2,
    'sort_keys': False
}

api.add_resource(VolumeList, '/volumes')
api.add_resource(Volume, '/volumes/<volume_id>')
