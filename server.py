from dnslib import A, CLASS, PTR, RCODE, RR, QTYPE
from dnslib.server import BaseResolver, DNSServer

from const import *
from models import FakeCache


class FakeResolver(BaseResolver):
    """Resolver object with reference to Server.cache so resolve() can interact with the cache"""

    def __init__(self, cache):
        self._cache = cache

    def resolve(self, request, handler):
        idna = request.q.qname.idna()

        self._cache.prune_stale()
        reply = request.reply()
        reply.header.rcode = RCODE.NOERROR

        if request.q.qtype == QTYPE.A:
            self._cache.add_record(idna)
            rec = self._cache.get_record_by_host(idna)
            reply.add_answer(RR(idna, rclass=CLASS.IN, rtype=QTYPE.A, rdata=A(rec)))
        elif request.q.qtype == QTYPE.PTR:
            rec = self._cache.get_record_by_ip(idna)
            reply.add_answer(RR(idna, rclass=CLASS.IN, rtype=QTYPE.PTR, rdata=PTR(rec)))
        else:
            reply.header.rcode = RCODE.SERVFAIL

        return reply


class FakeDNSServer(object):
    def __init__(self, addr=DEFAULT_LISTEN_ADDR, port=DEFAULT_LISTEN_PORT, duration=DEFAULT_CACHE_DURATION, ip_range=DEFAULT_ADDR_RANGE):
        self._addr = addr
        self._port = port

        self._cache = FakeCache(ip_range, duration)
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
    def addr_range(self):
        return self._cache.addr_range

    @addr_range.setter
    def addr_range(self, value):
        self._cache.addr_range = value

    def start(self):
        self._dns_server.start()

    def stop(self):
        self._dns_server.stop()
