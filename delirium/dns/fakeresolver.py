from dnslib.server import BaseResolver
#from dnslib.dns import RCODE
#from dnslib import QTYPE
from dnslib import *
import ipaddress

class FakeResolver(BaseResolver):

    """Resolver object with reference to Server.cache so resolve() can interact with the cache"""

    def __init__(self, cache):
        self._cache = cache

    @staticmethod
    def get_addr_from_reverse_pointer(arpa):
        ip_str = '.'.join(arpa.split('.')[:-3][::-1])  # strip in-addr.arpa./ip6.arpa., reverse order, join on '.'
        ip = ipaddress.ip_address(ip_str)

        if arpa.rstrip('.') != ip.reverse_pointer:
            raise ValueError("Reverse pointer provided didn't match the calculated pointer ({} != {})".format(arpa,
                             ip.reverse_pointer))

        return int(ip)

    def resolve(self, request, handler):
        # TODO: use the handler?
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
