import pytest
import time

import ipaddress

from delirium.const import *
from delirium.dns.resolver import DatabaseResolver


TEST_HOST = 'www.somedomain.tld'


@pytest.fixture()
def test_db():
    cache = DatabaseResolver(DEFAULT_SUBNET, duration=1)
    yield cache
    cache.drop_db()
    cache.close()


def test_cache_init(test_db: DatabaseResolver):
    assert test_db._ipv4network == ipaddress.IPv4Network(DEFAULT_SUBNET)


def test_cache_update(test_db):

    #  Test update of duration
    new_dur = 500
    test_db.duration = new_dur
    assert test_db.duration == new_dur

    # Test basic ability to change subnet
    new_subnet = '192.168.0.0/30'
    test_db.subnet = new_subnet
    assert test_db._ipv4network == ipaddress.IPv4Network(new_subnet)


def test_cache_update_subnet_during_use(test_db):
    test_db.subnet = '10.0.0.0/30'
    host_a = "www.a.com"
    host_b = "www.b.com"

    test_db.add_record(host_a)

    test_db.subnet = '10.0.0.0/30'
    test_db.add_record(host_b)

    assert test_db.get_addr_by_name(host_a) != test_db.get_addr_by_name(host_b)


@pytest.mark.xfail(reason="Not implemented yet")
def test_cache_duration(test_db):
    test_db.add_record(TEST_HOST)
    test_addr = test_db.get_addr_by_name(TEST_HOST)[0]
    assert test_addr > 0

    time.sleep(2)
    test_db.prune_stale()
    query_results = test_db.get_addr_by_name(TEST_HOST, True)
    assert query_results.pop() == test_addr

    #  Test infinite duration when duration = 0
    test_db.duration = 0
    test_db.add_record(TEST_HOST)
    test_addr = test_db.get_addr_by_name(TEST_HOST)[0]
    time.sleep(2)
    query_results = test_db.get_addr_by_name(TEST_HOST, False)
    assert query_results.pop() == test_addr


def test_pruning_behavior(test_db):
    test_db.add_record(TEST_HOST)
    test_addr = test_db.get_addr_by_name(TEST_HOST)[0]

    time.sleep(2)

    #  Test expiring of entries
    test_db.remove = False
    test_db.prune_stale()
    query_results = test_db.get_addr_by_name(TEST_HOST, expired=True)
    assert query_results.pop() == test_addr

    #  Test removal of entries
    test_db.remove = True
    assert test_db.remove is True
    test_db.prune_stale()
    query_results = test_db.get_addr_by_name(TEST_HOST, expired=True)
    assert query_results == []


def test_cache_range(test_db):
    test_db.add_record(TEST_HOST)
    addr = test_db.get_addr_by_name(TEST_HOST)[0]

    assert ipaddress.ip_address(addr) in test_db._ipv4network


def test_cache_regeneration(test_db):
    test_db.subnet = '10.0.0.0/30'
    host_a = "www.a.com"
    host_b = "www.b.com"
    host_c = "www.c.com"

    test_db.add_record(host_a)
    test_db.add_record(host_b)
    assert test_db.get_addr_by_name(host_a) != []
    with pytest.raises(IndexError):
        test_db.get_addr_by_name(host_c)[0]

    time.sleep(2)
    test_db.prune_stale()
    test_db.regenerate_hosts_pool()

    test_db.add_record(host_c)
    assert test_db.get_addr_by_name(host_c) != []


if __name__ == '__main__':
    pytest.main()
