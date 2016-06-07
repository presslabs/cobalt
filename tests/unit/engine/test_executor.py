# Copyright 2016 PressLabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pytest import mark

from engine import Executor
from tests.conftest import Dummy


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

    def test_reset(self, executor):
        executor._should_reset = False
        executor._watch_index = 1

        executor.reset()

        assert executor._should_reset
        assert executor._watch_index is None

    @mark.parametrize('volume,next_state', [
        [Dummy(value={'control': {'parent_id': ''},
                      'requested': {'reserved_size': 1},
                      'actual': {'reserved_size': 1}}), 'error'],
        [Dummy(value={'control': {'parent_id': ''},
                      'requested': {'reserved_size': 1},
                      'actual': {'reserved_size': 2}}), 'resizing'],
        [Dummy(value={'control': {'parent_id': '1'}}), 'cloning']
    ])
    def test_next_state(self, volume, next_state, executor):
        got_state = executor._next_state(volume)
        assert got_state == next_state

    def test_tick_with_reset(self, mocker, executor, p_executor_process, p_volume_manager_all):
        directory = mocker.MagicMock(etcd_index=0)
        volume = mocker.MagicMock()
        p_volume_manager_all.return_value = (directory, [volume])

        executor.tick()

        p_executor_process.assert_called_with(volume)
        assert p_volume_manager_all.called
        assert executor._volumes_to_process == []
        assert executor._watch_index == 1

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
