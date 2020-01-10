import os
import time
import unittest

from delirium.const import *
from delirium.dns.cache import get_addr_range
from delirium.dns.cache import CacheDatabase


def suite():
    cache_db_suite = unittest.TestLoader().loadTestsFromTestCase(TestCacheDatabase)
    return unittest.TestSuite(cache_db_suite)


class TestCacheDatabase(unittest.TestCase):
    TEST_HOST = 'www.somedomain.tld'

    def test_cache_init(self):
        c = CacheDatabase(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION, DEFAULT_DB_PATH)

        self.assertEqual(c.addr_range, get_addr_range(DEFAULT_ADDR_RANGE))
        self.assertEqual(c.duration, DEFAULT_CACHE_DURATION)

    def test_cache_update(self):
        c = CacheDatabase(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION, DEFAULT_DB_PATH)

        new_dur = 500
        c.duration = new_dur
        self.assertEqual(c.duration, new_dur)

        new_addr_range = '192.168.0.0-192.168.0.255'
        c.addr_range = new_addr_range
        self.assertEqual(c.addr_range, get_addr_range(new_addr_range))

    def test_cache_duration(self):
        c = CacheDatabase(DEFAULT_ADDR_RANGE, 1, DEFAULT_DB_PATH)
        c.add_record(self.TEST_HOST)

        self.assertTrue(c.get_addr_by_name(self.TEST_HOST))

        time.sleep(1)
        c.prune_stale()

        self.assertEqual(len(c.get_addr_by_name(self.TEST_HOST)), 0)

    def test_cache_range(self):
        c = CacheDatabase(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION, DEFAULT_DB_PATH)
        c.add_record(self.TEST_HOST)
        addr = c.get_addr_by_name(self.TEST_HOST)[0]

        self.assertTrue(c.addr_range[0] <= addr <= c.addr_range[1])


if __name__ == '__main__':
    unittest.main()
