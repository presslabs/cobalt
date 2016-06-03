from pytest import fixture, mark

from flask import Flask
from flask_restful import Api as FlaskRestful

from api import Api


@fixture
@mark.usefixtures('p_wsgi', 'p_create_app')
def api_service(volume_manager):
    return Api(volume_manager, {'host': '', 'port': 5000})


@fixture
def p_create_app(mocker, api_service, m_app):
    _create = mocker.patch.object(api_service, '_create_app')
    _create.return_value = m_app
    return _create


@fixture
def p_wsgi(mocker):
    return mocker.patch('gevent.pywsgi.WSGIServer')


@fixture
def m_app(mocker):
    return mocker.MagicMock(spec=Flask)


@fixture
def p_api_server(mocker, api_service):
    return mocker.patch.object(api_service, '_api_server')


@fixture
def p_register_resources(mocker):
    return mocker.patch.object(Api, '_api_server')


@fixture
def m_flask_restful(mocker):
    return mocker.MagicMock(spec=FlaskRestful)


@fixture
def p_flask_restful(mocker, m_flask_restful):
    patch = mocker.patch('api.api.RestApi')
    patch.return_value = m_flask_restful
    return patch
