import random
import socket
import struct
import time

from dnslib import RCODE, RR, A
from dnslib.server import BaseResolver, DNSServer


ADDR_RANGE_DEFAULT = '10.0.0.0-10.0.0.255'
CACHE_DURATION_DEFAULT = 900  # 15 minutes
LISTEN_ADDR_DEFAULT = '0.0.0.0'
LISTEN_PORT_DEFAULT = 53


def get_ip_ints(value):
    """Converts a <ip>-<ip> string to integers for random.randrange()"""

    values = value.split('-')
    s_int = struct.unpack('!L', socket.inet_aton(values[0]))[0]
    e_int = struct.unpack('!L', socket.inet_aton(values[1]))[0]
    return s_int, e_int


class FakeCache(object):
    """Provides a caching mechanism for the dnslib.DNSServer"""

    def __init__(self, addr_range=ADDR_RANGE_DEFAULT, duration=CACHE_DURATION_DEFAULT):
        self._duration = duration
        self._addr_range = get_ip_ints(addr_range)

        # TODO: use something better than a dict
        self._data = {}

    @property
    def data(self):
        return self._data

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def addr_range(self):
        return self._addr_range

    @addr_range.setter
    def addr_range(self, value):
        self._addr_range = get_ip_ints(value)

    def __get_random_ip(self):
        r_int = random.randrange(*self._addr_range)
        return socket.inet_ntoa(struct.pack('!L', r_int))

    def add_record(self, label):
        rec = self._data.get(label, {})
        if not rec:
            rec['ip'] = self.__get_random_ip()
        rec['time'] = time.time()
        self._data.update({label: rec})

    def get_record(self, label):
        return self._data.get(label)

    def prune_stale(self):
        to_del = []
        for k, v in self._data.items():
            if v['time'] <= time.time() - self._duration:
                to_del.append(k)
        for k in to_del:
            del self._data[k]


class FakeResolver(BaseResolver):
    """Resolver object with reference to Server.cache so resolve() can interact with the cache"""

    def __init__(self, cache):
        self._cache = cache

    def resolve(self, request, handler):
        self._cache.prune_stale()
        self._cache.add_record(request.q.qname.idna())
        rec = self._cache.get_record(request.q.qname.idna())

        reply = request.reply()
        reply.header.rcode = getattr(RCODE, 'NOERROR')
        a_rec = A(rec['ip'])
        reply.add_answer(RR(request.q.qname.idna(), rdata=a_rec))

        return reply


class FakeDNSServer(object):
    def __init__(self, addr=LISTEN_ADDR_DEFAULT, port=LISTEN_PORT_DEFAULT, duration=CACHE_DURATION_DEFAULT, ip_range=ADDR_RANGE_DEFAULT):
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


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('-l', '--listen', default=LISTEN_ADDR_DEFAULT, help='Address to listen on')
    p.add_argument('-p', '--port', default=LISTEN_PORT_DEFAULT, type=int, help='Purt to listen on (UDP)')
    p.add_argument('-t', '--time', default=CACHE_DURATION_DEFAULT, type=int, help='Seconds for which cache entries should exist')
    p.add_argument('-r', '--range', default=ADDR_RANGE_DEFAULT, help='Range of IP addresses to randomly generate')

    args = p.parse_args()

    s = FakeDNSServer(args.listen, args.port, args.time, args.range)

    try:
        s.start()
    except KeyboardInterrupt:
        pass
    finally:
        s.stop()
