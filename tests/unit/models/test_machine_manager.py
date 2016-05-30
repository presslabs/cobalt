from models import MachineManager, machine_schema


class TestMachineManager:
    def test_manchine_manager_class_vars(self):
        assert MachineManager.KEY == 'machines'
        assert MachineManager.SCHEMA == machine_schema
