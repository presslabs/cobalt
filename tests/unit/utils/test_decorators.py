from pytest import mark

from utils import inject_var, get_volume_or_404, have_state_or_409, inject_volume_manager
from tests.conftest import dummy_ready_volume


class TestDecorators:
    def test_inject_var(self):
        key = 'foo'
        value = 'bar'

        @inject_var(key, value)
        def test(foo):
            """Testing"""
            assert foo == value

        test()

        assert test.__doc__ == 'Testing'
        assert test.__name__ == 'test'

    @mark.parametrize('by_id_return', [None, {}])
    def test_get_volume_or_404(self, by_id_return, flask_app, p_volume_manager_by_id):
        p_volume_manager_by_id.return_value = by_id_return
        volume_id = '1'

        with flask_app.app_context():
            @get_volume_or_404(volume_id=volume_id)
            def test(volume):
                """Testing"""
                assert volume is not None
                assert volume == by_id_return

        result = test()
        if by_id_return is None:
            assert result == ({'message': 'Not Found'}, 404)

        assert test.__doc__ == 'Testing'
        assert test.__name__ == 'test'
        p_volume_manager_by_id.assert_called_with(volume_id)

    def test_inject_volume_manager(self, flask_app):

        @inject_volume_manager
        def test(volume_manager):
            """Testing"""
            assert volume_manager == flask_app.volume_manager

        with flask_app.app_context():
            test()

        assert test.__doc__ == 'Testing'
        assert test.__name__ == 'test'

    @mark.parametrize('state', ['ready', 'invalid'])
    def have_state_or_409(self, state):
        expected_state = 'ready'

        @have_state_or_409(dummy_ready_volume, expected_state)
        def test():
            """Testing"""

            assert state == expected_state

        result = test()
        if state != expected_state:
            assert result == ({'message': 'Resource not in state: {}'.format(expected_state)}, 409)

        assert test.__doc__ == 'Testing'
        assert test.__name__ == 'test'
