import threading

import time


class TestEngineIntegration:
    def test_2_engines(self, engine_factory):
        engine1 = engine_factory.get()
        engine2 = engine_factory.get()

        engine1._started = True
        engine2._started = True
        engine1.lease.lease_ttl = 1
        engine1.lease.refresh_ttl = 0.1
        engine2.lease.lease_ttl = 1
        engine2.lease.refresh_ttl = 0.1

        def engine_runner(engine):
            engine._run()

        def acquirer(engine):
            engine.lease.acquire()

        run1 = threading.Thread(target=engine_runner, args=[engine1])
        run2 = threading.Thread(target=engine_runner, args=[engine2])
        aq1 = threading.Thread(target=acquirer, args=[engine1])
        aq2 = threading.Thread(target=acquirer, args=[engine2])

        aq1.start()
        run1.start()
        time.sleep(0.1)
        aq2.start()
        run2.start()
        time.sleep(0.1)

        assert engine1.lease.is_held
        assert not engine2.lease.is_held

        assert engine1.stop()
        time.sleep(1.2)

        assert not engine1.lease.is_held
        assert engine2.lease.is_held

        assert engine2.stop()
        time.sleep(0.1)

        assert not engine2.lease.is_held

        threads = [run1, run2, aq1, aq2]
        for thread in threads:
            thread.join(5)

        if any(map(lambda x: x.is_alive(), threads)):
            assert False, 'Runner didn\'t stop in time'
