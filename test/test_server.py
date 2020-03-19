import ipaddress
import pytest
import socket


from delirium.const import *
from delirium.dns.server import FakeDNSServer


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
    yield FakeDNSServer(listen_port=PORT)


def test_server_init(test_server):
    assert test_server.port == PORT
    assert test_server.addr == DEFAULT_LISTEN_ADDR
    assert test_server._resolver._ipv4network == ipaddress.IPv4Network(DEFAULT_SUBNET)
    assert test_server.duration == DEFAULT_CACHE_DURATION


# noinspection PyPropertyAccess
def test_server_update(test_server):
    # really updating the FakeCache object but the server will proxy these
    new_dur = 500
    test_server.duration = new_dur
    assert test_server.duration == new_dur

    new_subnet = '192.168.0.0/24'
    test_server.subnet = new_subnet
    assert test_server._resolver._ipv4network == ipaddress.IPv4Network(new_subnet)

    with pytest.raises(AttributeError):
        test_server.port = _get_unused_udp_port()

    with pytest.raises(AttributeError):
        test_server.addr = '192.168.0.100'


def test_server_start(test_server):
    test_server.start_thread()
    assert test_server.is_alive() is True
    test_server.stop()


if __name__ == '__main__':
    pytest.main()
