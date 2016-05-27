from pytest import fixture


@fixture
def p_gevent_spawn(mocker):
    return mocker.patch('gevent.spawn')


@fixture
def p_time_sleep(mocker):
    return mocker.patch('time.sleep')
