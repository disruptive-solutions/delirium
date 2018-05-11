import dnslib
import socket
import unittest

from delirium.const import *
from delirium.models.cache import get_addr_range
from delirium.models.dictionary import CacheDictionary
from delirium.server import FakeDNSServer, FakeResolver


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


class TestFakeResolver(unittest.TestCase):
    TEST_HOST = 'www.somedomain.tld'

    def test_resolver_init(self):
        c = CacheDictionary(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION)
        FakeResolver(c)

    def test_resolver_A(self):
        c = CacheDictionary(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION)
        r = FakeResolver(c)

        cache_q = dnslib.DNSRecord().question(self.TEST_HOST)
        cache_rep = r.resolve(cache_q, handler=None)

        self.assertEqual(self.TEST_HOST, str(cache_rep.get_a().rname)[:-1])
        self.assertTrue(_is_valid_ip_addr(str(cache_rep.get_a().rdata)))

    def test_resolver_PTR(self):
        c = CacheDictionary(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION)
        r = FakeResolver(c)

        # copy from above to populate cache
        cache_q = dnslib.DNSRecord().question(self.TEST_HOST)
        cache_rep = r.resolve(cache_q, handler=None)
        cache_ip = str(cache_rep.get_a().rdata)
        cache_host = str(cache_rep.get_a().rname)

        ip_rev = '.'.join(cache_ip.split('.')[::-1])
        ptr = ip_rev + '.in-addr.arpa.'
        test_q = dnslib.DNSRecord().question(ptr, qtype='PTR')
        test_rep = r.resolve(test_q, handler=None)

        self.assertEqual(str(test_rep.get_a().rdata), cache_host)
        self.assertEqual(test_rep.get_a().rname, ptr)


if __name__ == '__main__':
    unittest.main()
