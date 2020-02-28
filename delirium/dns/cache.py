import datetime
import ipaddress
import socket
import struct

from delirium.const import DEFAULT_CACHE_DURATION, DEFAULT_DB_URI, DEFAULT_SUBNET
from delirium import database

from .models import DNSRecord


class AddressPoolDepletionError(Exception):
    pass


class CacheDatabase:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, subnet=DEFAULT_SUBNET, duration=DEFAULT_CACHE_DURATION, db_uri=DEFAULT_DB_URI, remove=False):
        self._remove_stale = remove
        self._db_engine = database.init_engine(db_uri)
        self._session = database.init_db(self._db_engine)
        self._duration = duration
        self._ipv4network = ipaddress.ip_network(subnet)
        self._hosts_pool = set(self._ipv4network.hosts())

    @property
    def remove(self):
        return self._remove_stale

    @remove.setter
    def remove(self, value):
        self._remove_stale = value

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def subnet(self):
        return str(self._ipv4network)

    @subnet.setter
    def subnet(self, value):
        self._ipv4network = ipaddress.ip_network(value)
        self.prune_stale()
        self.regenerate_hosts_pool()

    @staticmethod
    def __socket_aton(value):
        return struct.unpack('!L', socket.inet_aton(value))[0]

    def add_record(self, name):
        if not self._hosts_pool:
            self.regenerate_hosts_pool()

        try:
            return DNSRecord.add_or_update(self._session,
                                           name=name,
                                           duration=self.duration,
                                           ip_address=self._hosts_pool.pop())
        except KeyError as e:
            raise AddressPoolDepletionError("Entire address pool in use.") from e

    def regenerate_hosts_pool(self):
        active_recs = self._session.query(DNSRecord).filter_by(expired=False).all()
        active_addrs = {ipaddress.IPv4Address(rec.address) for rec in active_recs}
        all_addrs = set(self._ipv4network.hosts())
        self._hosts_pool = all_addrs - active_addrs

    def close(self):
        self._session.close()
        self._db_engine.dispose()

    def drop_db(self):
        database.drop_db(self._db_engine)

    def get_name_by_addr(self, addr, expired=False):
        records = self._session.query(DNSRecord).filter_by(address=addr, expired=expired).all()
        return [rec.name for rec in records]

    def get_addr_by_name(self, name, expired=False):
        records = self._session.query(DNSRecord).filter_by(name=name, expired=expired).all()
        return [rec.address for rec in records]

    def prune_stale(self):
        if self.remove:
            self._session.query(DNSRecord).filter(DNSRecord.expire_date <= datetime.datetime.now())\
                                          .delete()
        else:
            self._session.query(DNSRecord).filter(DNSRecord.expire_date <= datetime.datetime.now())\
                                          .update({'expired': True})
        self._session.commit()
