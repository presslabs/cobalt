from pytest import fixture


@fixture
def gevent_spawn(mocker):
    return mocker.patch('gevent.spawn')


@fixture
def gevent(mocker):
    return mocker.patch('time.sleep')