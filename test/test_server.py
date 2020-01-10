import dnslib
import socket
import unittest

from delirium.const import *
from delirium.dns.fakednsserver import FakeDNSServer
from delirium.dns.fakeresolver import FakeResolver
from delirium.dns.cache import get_addr_range


def suite():
    server_suite = unittest.TestLoader().loadTestsFromTestCase(TestFakeDNSServer)
    resolver_suite = unittest.TestLoader().loadTestsFromTestCase(TestFakeResolver)
    return unittest.TestSuite([server_suite, resolver_suite])


def _get_unused_udp_port():
    """Returns available UDP port"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _is_valid_ip_addr(addr):
    try:
        socket.inet_aton(addr)
    except socket.error:
        return False
    else:
        return True


class TestFakeDNSServer(unittest.TestCase):
    PORT = _get_unused_udp_port()  # can't bind to anything south of 1024 without root (default 53)

    def test_server_init(self):
        s = FakeDNSServer(port=self.PORT)

        self.assertEqual(s.port, self.PORT)
        self.assertEqual(s.addr, DEFAULT_LISTEN_ADDR)
        self.assertEqual(s.addr_range, get_addr_range(DEFAULT_ADDR_RANGE))
        self.assertEqual(s.duration, DEFAULT_CACHE_DURATION)

    # noinspection PyPropertyAccess
    def test_server_update(self):
        s = FakeDNSServer(port=self.PORT)

        # reallu updating the FakeCache object but the server will proxy these
        new_dur = 500
        s.duration = new_dur
        self.assertEqual(s.duration, new_dur)

        new_addr_range = '192.168.0.0-192.168.0.255'
        s.addr_range = new_addr_range
        self.assertEqual(s.addr_range, get_addr_range(new_addr_range))

        with self.assertRaises(AttributeError):
            s.cache = {}

        with self.assertRaises(AttributeError):
            s.port = _get_unused_udp_port()

        with self.assertRaises(AttributeError):
            s.addr = '192.168.0.100'

    def test_server_start(self):
        # TODO: this could probably be improved
        s = FakeDNSServer(port=self.PORT)
        s.start_thread()
        self.assertTrue(s.is_alive())
        s.stop()


if __name__ == '__main__':
    unittest.main()
