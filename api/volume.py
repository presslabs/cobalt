from flask import Blueprint, jsonify

volume_blueprint = Blueprint('volume', __name__)


@volume_blueprint.route('/')
@volume_blueprint.route('/<volume_id>')
def get(volume_id=None):
    return jsonify(**{'error': 'volume_id {}'.format(volume_id)})


@volume_blueprint.route('/', methods=['POST'])
def create():
    pass


@volume_blueprint.route('/<volume_id>', methods=['DELETE'])
def delete(volume_id=None):
    pass


@volume_blueprint.route('/<volume_id>', methods=['PUT'])
def update(volume_id=None):
    pass
