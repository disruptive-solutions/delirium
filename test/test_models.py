import socket
import struct
import time
import unittest

from fake_dns.const import *
from fake_dns.models import FakeCache, _get_ip_ints


def suite():
    cache_suite = unittest.TestLoader().loadTestsFromTestCase(TestFakeCache)
    return unittest.TestSuite(cache_suite)


class TestFakeCache(unittest.TestCase):
    TEST_HOST = 'www.somedomain.tld'

    def test_cache_init(self):
        c = FakeCache()

        self.assertEqual(c.addr_range, _get_ip_ints(DEFAULT_ADDR_RANGE))
        self.assertEqual(c.duration, DEFAULT_CACHE_DURATION)

    # noinspection PyPropertyAccess
    def test_cache_update(self):
        c = FakeCache()

        new_dur = 500
        c.duration = new_dur
        self.assertEqual(c.duration, new_dur)

        new_addr_range = '192.168.0.0-192.168.0.255'
        c.addr_range = new_addr_range
        self.assertEqual(c.addr_range, _get_ip_ints(new_addr_range))

        with self.assertRaises(AttributeError):
            c.data = {}

    def test_cache_timeout(self):
        c = FakeCache(duration=1)
        c.add_record(self.TEST_HOST)

        self.assertTrue(c.get_record_by_host(self.TEST_HOST))

        time.sleep(1)
        c.prune_stale()

        with self.assertRaises(AttributeError):
            self.assertFalse(c.get_record_by_host(self.TEST_HOST))

    def test_cache_range(self):
        c = FakeCache()
        c.add_record(self.TEST_HOST)
        ip = c.get_record_by_host(self.TEST_HOST)
        ip_int = struct.unpack('!L', socket.inet_aton(ip))[0]

        self.assertTrue(c.addr_range[0] <= ip_int <= c.addr_range[1])


if __name__ == '__main__':
    unittest.main()
