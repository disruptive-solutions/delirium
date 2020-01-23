import ipaddress

from dnslib.server import BaseResolver
from dnslib import A, CLASS, PTR, RCODE, RR, QTYPE


class FakeResolver(BaseResolver):
    """Resolver object with reference to Server.cache so resolve() can interact with the cache"""

    def __init__(self, cache):
        self._cache = cache

    @staticmethod
    def get_addr_from_reverse_pointer(arpa):
        ip_str = '.'.join(arpa.split('.')[:-3][::-1])  # strip in-addr.arpa./ip6.arpa., reverse order, join on '.'
        ip_obj = ipaddress.ip_address(ip_str)

        if arpa.rstrip('.') != ip_obj.reverse_pointer:
            raise ValueError(f"Provided pointer doesn't match real pointer ({arpa} != {ip_obj.reverse_pointer})")

        return int(ip_obj)

    def resolve(self, request, handler):
        idna = request.q.qname.idna()

        self._cache.prune_stale()
        reply = request.reply()
        reply.header.rcode = RCODE.NXDOMAIN

        if request.q.qtype == QTYPE.A:
            self._cache.add_record(idna)
            for rec in self._cache.get_addr_by_name(idna):
                addr = ipaddress.ip_address(rec)
                reply.add_answer(RR(idna, rclass=CLASS.IN, rtype=QTYPE.A, rdata=A(str(addr))))
        elif request.q.qtype == QTYPE.PTR:
            addr = self.get_addr_from_reverse_pointer(idna)
            for rec in self._cache.get_name_by_addr(addr):
                reply.add_answer(RR(idna, rclass=CLASS.IN, rtype=QTYPE.PTR, rdata=PTR(rec)))

        if reply.rr:
            reply.header.rcode = RCODE.NOERROR

        return reply
