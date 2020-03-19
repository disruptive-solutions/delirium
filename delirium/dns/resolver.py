import logging
import socket
import struct

from typing import AnyStr, List

import ipaddress

from dnslib.dns import A, CLASS, PTR, QTYPE, RCODE, RR
from dnslib.server import BaseResolver

from delirium.const import DEFAULT_CACHE_DURATION, DEFAULT_DB_URI
from delirium import database

from . import models


class AddressPoolDepletionError(Exception):
    pass


class DatabaseResolver(BaseResolver):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, subnet, *,
                 duration=DEFAULT_CACHE_DURATION, db_path=DEFAULT_DB_URI, remove=False, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self._remove_stale = remove
        self._db_engine = database.init_engine(db_path)
        self._session = database.init_db(self._db_engine)
        self._duration = duration
        self._ipv4network = ipaddress.ip_network(subnet)
        self._hosts_pool = set(self._ipv4network.hosts())

    @property
    def remove(self):
        return self._remove_stale

    @remove.setter
    def remove(self, value):
        self.logger.debug('Cache Update - Delete stale records: %s', value)
        self._remove_stale = value

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self.logger.debug('Cache Update - Record life now %s seconds', value)
        self._duration = value

    @property
    def subnet(self):
        return str(self._ipv4network)

    @subnet.setter
    def subnet(self, value):
        self.logger.debug('Cache Update - Subnet now %s', ipaddress.ip_network(value))
        self._ipv4network = ipaddress.ip_network(value)
        self.prune_stale()
        self.regenerate_hosts_pool()

    @staticmethod
    def __socket_aton(value):
        return struct.unpack('!L', socket.inet_aton(value))[0]

    def add_record(self, name: str) -> object:
        if not self._hosts_pool:
            self.regenerate_hosts_pool()

        try:
            return models.add_or_update_record(self._session,
                                               name=name,
                                               duration=self.duration,
                                               ip_address=self._hosts_pool.pop())
        except KeyError as e:
            self.logger.info('No addresses left in pool')
            raise AddressPoolDepletionError("Entire address pool in use.") from e

    def regenerate_hosts_pool(self):
        self.logger.debug('Regenerating hosts pool')
        active_recs = models.get_records(self._session, expired=False)
        active_addrs = {ipaddress.IPv4Address(rec.address) for rec in active_recs}
        all_addrs = set(self._ipv4network.hosts())
        self._hosts_pool = all_addrs - active_addrs
        self.logger.debug('Recovered %d stale addresses', len(self._hosts_pool))

    def close(self):
        self.logger.debug('Closing database connection')
        self._session.close()
        self._db_engine.dispose()

    def drop_db(self):
        self.logger.debug('Dropping database tables')
        database.drop_db(self._db_engine)

    def get_name_by_addr(self, addr: int, *, expired: bool = False) -> List[AnyStr]:
        self.logger.debug("Fetching records for '%s'", ipaddress.IPv4Address(addr))
        records = models.get_records(self._session, address=addr, expired=expired)
        return [rec.name for rec in records]

    def get_addr_by_name(self, name: str, *, expired: bool = False) -> List[AnyStr]:
        self.logger.debug("Fetching records for '%s'", name)
        records = models.get_records(self._session, name=name, expired=expired)
        return [rec.address for rec in records]

    def prune_stale(self):
        self.logger.debug('Pruning stale records')
        if self.remove:
            models.delete_record(self._session)
        else:
            models.mark_record_expired(self._session)

    @staticmethod
    def get_addr_from_reverse_pointer(arpa):
        ip_str = '.'.join(arpa.split('.')[:-3][::-1])  # strip in-addr.arpa./ip6.arpa., reverse order, join on '.'
        ip_obj = ipaddress.ip_address(ip_str)

        if arpa.rstrip('.') != ip_obj.reverse_pointer:
            raise ValueError(f"Provided pointer doesn't match real pointer ({arpa} != {ip_obj.reverse_pointer})")

        return int(ip_obj)

    def resolve(self, request, handler):
        idna = request.q.qname.idna()

        self.prune_stale()
        reply = request.reply()
        reply.header.rcode = RCODE.NXDOMAIN

        if request.q.qtype == QTYPE.A:
            try:
                self.add_record(idna)
            except AddressPoolDepletionError:
                reply.header.rcode = RCODE.SERVFAIL

            for rec in self.get_addr_by_name(idna):
                addr = ipaddress.ip_address(rec)
                reply.add_answer(RR(idna, rclass=CLASS.IN, rtype=QTYPE.A, rdata=A(str(addr))))
        elif request.q.qtype == QTYPE.PTR:
            addr = self.get_addr_from_reverse_pointer(idna)
            for rec in self.get_name_by_addr(addr):
                reply.add_answer(RR(idna, rclass=CLASS.IN, rtype=QTYPE.PTR, rdata=PTR(rec)))

        if reply.rr:
            reply.header.rcode = RCODE.NOERROR

        return reply
