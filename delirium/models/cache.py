import itertools
import socket
import struct

from abc import ABCMeta, abstractmethod


def get_addr_range(value):
    """Converts a <ip>-<ip> string to integers for random.randrange()"""

    values = value.split('-')
    s_int = struct.unpack('!L', socket.inet_aton(values[0]))[0]
    e_int = struct.unpack('!L', socket.inet_aton(values[1]))[0]
    return s_int, e_int


def n_generator(start, end):
    for i in itertools.cycle(range(start, end + 1)):
        yield i


class CacheObject:
    __metaclass__ = ABCMeta

    def __init__(self, addr_range, duration):
        self._addr_range = get_addr_range(addr_range)
        self._duration = duration
        self._n_generator = n_generator(*self._addr_range)

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
        self._addr_range = get_addr_range(value)

    @staticmethod
    def __socket_aton(value):
        return struct.unpack('!L', socket.inet_aton(value))[0]

    @abstractmethod
    def add_record(self, label):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_addr_by_name(self, value):
        pass

    @abstractmethod
    def get_name_by_addr(self, value):
        pass

    @abstractmethod
    def prune_stale(self):
        pass
