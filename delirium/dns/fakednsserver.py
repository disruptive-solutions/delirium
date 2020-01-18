from dnslib.server import DNSServer

from delirium.const import *
from .fakeresolver import FakeResolver
from .cache import CacheDatabase


class FakeDNSServer(object):
    def __init__(self, addr=DEFAULT_LISTEN_ADDR, port=DEFAULT_LISTEN_PORT, duration=DEFAULT_CACHE_DURATION,
                 ip_range=DEFAULT_SUBNET, cache_path=DEFAULT_DB_PATH):
        self._addr = addr
        self._port = port

        self._cache = CacheDatabase(ip_range, duration, cache_path)
        self._resolver = FakeResolver(self._cache)
        self._dns_server = DNSServer(self._resolver, self._addr, self._port)

    @property
    def cache(self):
        return self._cache

    @property
    def addr(self):
        return self._addr

    @property
    def port(self):
        return self._port

    @property
    def duration(self):
        return self._cache.duration

    @duration.setter
    def duration(self, value):
        self._cache.duration = value

    @property
    def subnet(self):
        return self._cache.subnet

    @subnet.setter
    def subnet(self, value):
        self._cache.subnet = value

    def is_alive(self):
        return self._dns_server.isAlive()

    def start(self):
        self._dns_server.start()

    def start_thread(self):
        self._dns_server.start_thread()

    def stop(self):
        self._cache.close()
        self._dns_server.stop()
