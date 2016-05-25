from utils import Connection


class TestConnection:
    def test_connection_is_tuple(self):
        con = Connection('', 5000)
        assert isinstance(con, tuple)
