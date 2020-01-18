import ipaddress
import itertools
import socket
import sqlite3
import struct
import time


QUERY_CREATE_TABLE = """CREATE TABLE IF NOT EXISTS cache (
                            id integer PRIMARY KEY AUTOINCREMENT,
                            addr integer NOT NULL,
                            name text NOT NULL,
                            date real NOT NULL,
                            expired integer DEFAULT 0
                        );"""

QUERY_ADD_ENTRY = "INSERT INTO cache (addr, name, date) VALUES (:addr, :name, :date);"
QUERY_EXPIRE_DELETE_BY_ID = "DELETE FROM cache WHERE id = (?);"
QUERY_EXPIRE_UPDATE_BY_ID = "UPDATE cache SET expired = 1 WHERE id = (?);"
QUERY_GET_BY_EXPIRED = "SELECT * FROM cache WHERE expired = :expired;"
QUERY_GET_BY_ADDR = "SELECT * FROM cache WHERE addr = :addr AND expired = :expired;"
QUERY_GET_BY_NAME = "SELECT * FROM cache WHERE name = :name AND expired = :expired;"
QUERY_UPDATE_DATE_BY_ID = "UPDATE cache SET date = :date WHERE id = :id;"


def init_db(path):
    c = sqlite3.connect(path, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute(QUERY_CREATE_TABLE)
    return c


class CacheDatabase:
    def __init__(self, subnet, duration, path):
        self.remove_stale = False
        self._path = path
        self._conn = init_db(self._path)
        self._cur = self._conn.cursor()
        self._duration = duration
        self._ipv4network = ipaddress.IPv4Network(subnet)
        self._addr_cycle = itertools.cycle(self._ipv4network)

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
        self._ipv4network = ipaddress.IPv4Network(value)
        self._addr_cycle = itertools.cycle(self._ipv4network)

    @staticmethod
    def __socket_aton(value):
        return struct.unpack('!L', socket.inet_aton(value))[0]

    @property
    def path(self):
        return self._path

    def add_record(self, name):
        self._cur.execute(QUERY_GET_BY_NAME, {'name': name, 'expired': 0})
        rec = self._cur.fetchone()

        if rec:
            q = QUERY_UPDATE_DATE_BY_ID
            p = {'id': rec['id'], 'date': time.time()}
        else:
            q = QUERY_ADD_ENTRY
            p = {'addr': int(next(self._addr_cycle)), 'name': name, 'date': time.time()}

        self._cur.execute(q, p)
        self._conn.commit()

    def close(self):
        self._cur.close()
        self._conn.commit()
        self._conn.close()

    def get_name_by_addr(self, addr, expired=0):
        self._cur.execute(QUERY_GET_BY_ADDR, {'addr': addr, 'expired': expired})

        out = []
        for rec in self._cur:
            out.append(rec['id'])

        return out

    def get_addr_by_name(self, name, expired=0):
        self._cur.execute(QUERY_GET_BY_NAME, {'name': name, 'expired': expired})

        out = []
        for rec in self._cur:
            out.append(rec['addr'])

        return out

    def prune_stale(self):
        self._cur.execute(QUERY_GET_BY_EXPIRED, {'expired': 0})
        ids = []

        for row in self._cur:
            ids.append((row['id'],))  # executemany() seq_of_parameters should be a tuple (1-tuple in this case)

        if self.remove_stale:
            q = QUERY_EXPIRE_DELETE_BY_ID
        else:
            q = QUERY_EXPIRE_UPDATE_BY_ID

        self._cur.executemany(q, ids)
        self._conn.commit()
