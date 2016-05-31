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

    def test_tick_with_reset_no_dir(self, mocker, executor, p_executor_process, p_volume_manager_all):
        volume = mocker.MagicMock()
        p_volume_manager_all.return_value = (None, [volume])

        executor.tick()

        p_executor_process.assert_called_with(volume)
        assert p_volume_manager_all.called
        assert executor._volumes_to_process == []
        assert executor._watch_index is None

    @mark.parametrize('initial_index', [None, 1])
    def test_tick_watch_initial_index(self, mocker, executor, p_executor_process, p_volume_manager_all,
                                      p_volume_manager_watch, initial_index):
        index = 2
        volume = mocker.MagicMock(modifiedIndex=2)
        p_volume_manager_all.return_value = (None, [])
        p_volume_manager_watch.return_value = volume

        executor._watch_index = initial_index
        executor.tick()

        p_executor_process.assert_called_with(volume)
        p_volume_manager_watch.assert_called_with(index=initial_index, timeout=executor.delay)
        assert p_volume_manager_all.called
        assert executor._watch_index == index + 1

    def test_tick_watch_timeout(self, mocker, executor, p_executor_process, p_volume_manager_all,
                                p_volume_manager_watch):
        p_volume_manager_all.return_value = (None, [])
        p_volume_manager_watch.return_value = None
        executor.reset = mocker.MagicMock()

        executor.tick()

        p_volume_manager_watch.assert_called_with(index=None, timeout=executor.delay)
        assert p_volume_manager_all.called
        assert executor.reset.called
        assert not p_executor_process.called

    def test_get_active_machines(self, mocker, executor, p_machine_manager_all):
        machine = mocker.MagicMock(key=1)
        p_machine_manager_all.return_value = (None, [machine])

        active = executor.get_active_machine_keys()

        assert active == [machine.key]
