import ipaddress
import os
import pytest
import time

from delirium.const import *
from delirium.dns.cache import CacheDatabase


@pytest.fixture()
def test_db():
    yield CacheDatabase(DEFAULT_SUBNET, DEFAULT_CACHE_DURATION, DEFAULT_DB_PATH)


class TestCacheDatabase():
    TEST_HOST = 'www.somedomain.tld'

    def test_cache_init(self, test_db):
        assert test_db._ipv4network == ipaddress.IPv4Network(DEFAULT_SUBNET)
        assert test_db.duration == DEFAULT_CACHE_DURATION

    def test_cache_update(self, test_db):
        new_dur = 500
        test_db.duration = new_dur
        assert test_db.duration == new_dur

        new_subnet = '192.168.0.0/24'
        test_db.subnet = new_subnet
        assert test_db._ipv4network == ipaddress.IPv4Network(new_subnet)

    def test_cache_duration(self, test_db):
        test_db.add_record(self.TEST_HOST)

        assert test_db.get_addr_by_name(self.TEST_HOST)[0] > 0

        time.sleep(1)
        test_db.prune_stale()

        assert len(test_db.get_addr_by_name(self.TEST_HOST)) == 0

    def test_cache_range(self, test_db):
        test_db.add_record(self.TEST_HOST)
        addr = test_db.get_addr_by_name(self.TEST_HOST)[0]

        assert ipaddress.ip_address(addr) in test_db._ipv4network


if __name__ == '__main__':
    pytest.main()
