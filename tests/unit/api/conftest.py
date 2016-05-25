from pytest import fixture

from flask import Flask

from api.api import Api


@fixture
def api_service(api_app):
    return Api(api_app)


@fixture
def api_app(mocker):
    return mocker.MagicMock(spec=Flask)


@fixture
def api_server(mocker, api_service):
    return mocker.patch.object(api_service, '_api_server')


@fixture
def gevent_spawn(mocker):
    return mocker.patch('gevent.spawn')
