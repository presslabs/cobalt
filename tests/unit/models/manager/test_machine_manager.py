from models.manager import MachineManager


class TestMachineManager:
    def test_manchine_manager_class_vars(self):
        assert MachineManager.KEY == 'machines'
