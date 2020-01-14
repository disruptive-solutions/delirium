import dnslib
import socket
import pytest

from delirium.const import *
from delirium.dns.fakednsserver import FakeDNSServer
from delirium.dns.fakeresolver import FakeResolver
from delirium.dns.cache import get_addr_range


def _get_unused_udp_port():
    """Returns available UDP port"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


PORT = _get_unused_udp_port()


@pytest.fixture()
def test_server():
    yield FakeDNSServer(port=PORT)


def _is_valid_ip_addr(addr):
    try:
        socket.inet_aton(addr)
    except socket.error:
        return False
    else:
        return True


class TestFakeDNSServer():
    def test_server_init(self, test_server):
        assert test_server.port == PORT
        assert test_server.addr == DEFAULT_LISTEN_ADDR
        assert test_server.addr_range == get_addr_range(DEFAULT_ADDR_RANGE)
        assert test_server.duration == DEFAULT_CACHE_DURATION

    # noinspection PyPropertyAccess
    def test_server_update(self, test_server):
        # really updating the FakeCache object but the server will proxy these
        new_dur = 500
        test_server.duration = new_dur
        assert test_server.duration == new_dur

        new_addr_range = '192.168.0.0-192.168.0.255'
        test_server.addr_range = new_addr_range
        assert test_server.addr_range == get_addr_range(new_addr_range)

        with pytest.raises(AttributeError):
            test_server.cache = {}

        with pytest.raises(AttributeError):
            test_server.port = _get_unused_udp_port()

        with pytest.raises(AttributeError):
            test_server.addr = '192.168.0.100'

    def test_server_start(self, test_server):
        test_server.start_thread()
        assert test_server.is_alive() == True
        test_server.stop()


if __name__ == '__main__':
    pytest.main()
