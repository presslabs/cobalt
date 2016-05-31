from pytest import mark

from engine import Executor


class TestExecutor:
    def test_initial_state(self, executor, volume_manager, machine_manager):
        assert executor.volume_manager == volume_manager
        assert executor.machine_manager == machine_manager
        assert executor.delay == 0

        assert executor._should_reset
        assert executor._volumes_to_process == []
        assert executor._watch_index is None

    @mark.parametrize('context', [{'timeout': 'a'}, {}])
    def test_initial_state_wrong_timeout(self, context, volume_manager, machine_manager, p_print):
        executor = Executor(volume_manager, machine_manager, context)

        assert executor.delay == 10
        assert p_print.called

    def test_timeout(self, executor, p_time_sleep):
        executor.timeout()

        p_time_sleep.assert_called_with(executor.delay)

    def reset(self, executor):
        executor._should_reset = False
        executor._watch_index = 1

        executor.reset()

        assert executor._should_reset
        assert executor._watch_index is None

    def test_tick_with_reset(self, mocker, executor, p_executor_process, p_volume_manager_all):
        directory = mocker.MagicMock(etcd_index=0)
        volume = mocker.MagicMock()
        p_volume_manager_all.return_value = (directory, [volume])

        executor.tick()

        p_executor_process.assert_called_with(volume)
        assert p_volume_manager_all.called
        assert executor._volumes_to_process == []
        assert executor._watch_index == 0
