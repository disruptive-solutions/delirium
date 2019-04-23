from delirium.const import *
from delirium.server import FakeDNSServer


def cli_app():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('-l', '--listen', default=DEFAULT_LISTEN_ADDR, help='Address to listen on')
    p.add_argument('-p', '--port', default=DEFAULT_LISTEN_PORT, type=int, help='Purt to listen on (UDP)')
    p.add_argument('-t', '--time', default=DEFAULT_CACHE_DURATION, type=int,
                   help='Seconds for which cache entries should exist')
    p.add_argument('-r', '--range', default=DEFAULT_ADDR_RANGE, help='Range of IP addresses to randomly generate')
    p.add_argument('--db-path', help='Path to sqlite3 database')

    args = p.parse_args()

    if args.db_path:  # there's probably a better way to do this
        cache_type = CACHE_TYPE.DATABASE
    else:
        cache_type = CACHE_TYPE.DICTIONARY

    s = FakeDNSServer(args.listen, args.port, args.time, args.range, cache_type, args.db_path)

    try:
        s.start()
    except KeyboardInterrupt:
        pass
    finally:
        s.stop()
