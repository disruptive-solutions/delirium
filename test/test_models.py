import os
import time
import pytest

from delirium.const import *
from delirium.dns.cache import get_addr_range
from delirium.dns.cache import CacheDatabase

@pytest.fixture()
def test_db():
    yield CacheDatabase(DEFAULT_ADDR_RANGE, DEFAULT_CACHE_DURATION, DEFAULT_DB_PATH)


@pytest.mark.usefixtures('test_db')
class TestCacheDatabase():
    TEST_HOST = 'www.somedomain.tld'

    def test_cache_init(self, test_db):
        assert test_db.addr_range == get_addr_range(DEFAULT_ADDR_RANGE)
        assert test_db.duration == DEFAULT_CACHE_DURATION

    def test_cache_update(self, test_db):
        new_dur = 500
        test_db.duration = new_dur
        assert test_db.duration == new_dur

        new_addr_range = '192.168.0.0-192.168.0.255'
        test_db.addr_range = new_addr_range
        assert test_db.addr_range == get_addr_range(new_addr_range)

    def test_cache_duration(self, test_db):
        test_db.duration = 1
        test_db.add_record(self.TEST_HOST)

        assert test_db.get_addr_by_name(self.TEST_HOST)[0] > 0

        time.sleep(1)
        test_db.prune_stale()

        assert len(test_db.get_addr_by_name(self.TEST_HOST)) == 0

    def test_cache_range(self, test_db):
        test_db.add_record(self.TEST_HOST)
        addr = test_db.get_addr_by_name(self.TEST_HOST)[0]

        assert (test_db.addr_range[0] <= addr <= test_db.addr_range[1]) == True


if __name__ == '__main__':
    pytest.main()
