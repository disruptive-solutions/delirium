import random
import socket
import struct
import time

from const import *


def _get_ip_ints(value):
    """Converts a <ip>-<ip> string to integers for random.randrange()"""

    values = value.split('-')
    s_int = struct.unpack('!L', socket.inet_aton(values[0]))[0]
    e_int = struct.unpack('!L', socket.inet_aton(values[1]))[0]
    return s_int, e_int


class FakeCache(object):
    """Provides a caching mechanism for the dnslib.DNSServer"""

    def __init__(self, addr_range=DEFAULT_ADDR_RANGE, duration=DEFAULT_CACHE_DURATION):
        self._duration = duration
        self._addr_range = _get_ip_ints(addr_range)

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
        self._addr_range = _get_ip_ints(value)

    def __get_random_ip(self):
        r_int = random.randrange(*self._addr_range)
        return socket.inet_ntoa(struct.pack('!L', r_int))

    def add_record(self, label):
        rec = self._data.get(label, {})
        if not rec:
            ip_parts = self.__get_random_ip().split('.')
            rec['ip'] = '.'.join(ip_parts)
            rec['ptr'] = '.'.join(ip_parts[::-1]) + '.in-addr.arpa.'
        rec['time'] = time.time()
        self._data.update({label: rec})

    def get_record_by_host(self, value):
        return self._data.get(value).get('ip')

    def get_record_by_ip(self, value):
        for k, v in self._data.items():
            if v['ptr'] == value:
                return k

    def prune_stale(self):
        to_del = []
        for k, v in self._data.items():
            if v['time'] <= time.time() - self._duration:
                to_del.append(k)
        for k in to_del:
            del self._data[k]
