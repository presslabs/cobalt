import pytest

from cobalt import generate_context


@pytest.fixture
def config_defaults():
    return {
        'test': 'test',
        'key': {
            'nested': 'test'
        },
        'array': [1, 2, 3],
        'empty': None
    }


class TestConfig:
    def test_empty_user_config(self, config_defaults):
        output = generate_context(config_defaults, {})

        assert output == config_defaults

    def test_generation_result_unlinked_inputs(self, config_defaults):
        output = generate_context(config_defaults, {})

        config_defaults['test'] = 1
        assert not config_defaults['test'] == output['test']

        config_defaults['test'] = 'test'
        output = generate_context({}, config_defaults)

        config_defaults['test'] = 1
        assert not config_defaults['test'] == output['test']

        # currently if the user dict contains data not present in the defaults they persist -> splats (**)
        # will fail
