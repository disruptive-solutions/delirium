import logging
import sys

from logging import Formatter, Logger, StreamHandler
from logging.handlers import RotatingFileHandler

from dnslib import QTYPE, RCODE
from dnslib.server import DNSServer

from delirium import const
from .resolver import DatabaseResolver


DEFAULT_LOGGER_FMT = '%(asctime)s [%(name)s %(process)d] - %(levelname)s - %(message)s'


class DeliriumDNSLogger(Logger):
    def __init__(self, *, level=logging.INFO, path=None, fmt=DEFAULT_LOGGER_FMT):
        super().__init__('delirium.dns')

        if path:
            handler = RotatingFileHandler(path, maxBytes=2**18, backupCount=3)
        else:
            handler = StreamHandler(sys.stdout)

        self.formatter = Formatter(fmt)
        handler.setFormatter(self.formatter)
        self.addHandler(handler)
        self.setLevel(level)

    def log_recv(self, handler, data):
        pass

    def log_send(self, handler, data):
        pass

    def log_request(self, handler, request):
        self.info("Request: [%s:%d] (%s) / '%s' (%s)",
                  handler.client_address[0],
                  handler.client_address[1],
                  handler.protocol,
                  request.q.qname,
                  QTYPE[request.q.qtype])

    def log_reply(self, handler, reply):
        elements = [handler.client_address[0], handler.client_address[1],
                    handler.protocol, reply.q.qname, QTYPE[reply.q.qtype]]
        if reply.header.rcode == RCODE.NOERROR:
            elements.append(",".join([QTYPE[a.rtype] for a in reply.rr]))
        else:
            elements.append(RCODE[reply.header.rcode])
        self.info("Reply: [%s:%d] (%s) / '%s' (%s) / %s", *elements)

    def log_truncated(self, handler, reply):
        self.info("Truncated Reply: [%s:%d] (%s) / '%s' (%s) / RRs: %s",
                  handler.client_address[0],
                  handler.client_address[1],
                  handler.protocol,
                  reply.q.qname,
                  QTYPE[reply.q.qtype],
                  ",".join([QTYPE[a.rtype] for a in reply.rr]))

    def log_error(self, handler, e):
        self.error("Invalid Request: [%s:%d] (%s) :: %s",
                   handler.client_address[0],
                   handler.client_address[1],
                   handler.protocol,
                   e)


class FakeDNSServer:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    def __init__(self, listen_addr=const.DEFAULT_LISTEN_ADDR, listen_port=const.DEFAULT_LISTEN_PORT,
                 *, record_life=const.DEFAULT_CACHE_DURATION, subnet=const.DEFAULT_SUBNET,
                 db_path=const.DEFAULT_DB_URI, remove_records=False, logger=None):
        self.logger = logger or DeliriumDNSLogger()
        self._addr = listen_addr
        self._port = listen_port
        self._resolver = DatabaseResolver(subnet,
                                          db_path=db_path,
                                          duration=record_life,
                                          remove=remove_records,
                                          logger=self.logger)
        self._dns_server = DNSServer(self._resolver,
                                     self._addr,
                                     self._port,
                                     logger=self.logger)

    @property
    def addr(self):
        return self._addr

    @property
    def port(self):
        return self._port

    @property
    def duration(self):
        return self._resolver.duration

    @duration.setter
    def duration(self, value):
        self.logger.debug('Setting cache duration to %s', value)
        self._resolver.duration = value

    @property
    def subnet(self):
        return self._resolver.subnet

    @subnet.setter
    def subnet(self, value):
        self.logger.debug('Setting cache subnet to %s', value)
        self._resolver.subnet = value

    def is_alive(self):
        return self._dns_server.isAlive()

    def start(self):
        self.logger.info('Starting Delirium DNS Server')
        self._dns_server.start()

    def start_thread(self):
        self._dns_server.start_thread()

    def stop(self):
        self.logger.info('Stopping Delerium DNS Server')
        self._resolver.close()
        self._dns_server.stop()
