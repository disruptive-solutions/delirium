import click

from .const import *
from .dns import FakeDNSServer


@click.group()
def delirium():
    pass


@click.command()
@click.option('-l', '--laddr', default=DEFAULT_LISTEN_ADDR, help='Address to listen on')
@click.option('-p', '--lport', default=DEFAULT_LISTEN_PORT, type=int, help='Port to listen on (UDP)')
@click.option('-t', '--time', default=DEFAULT_CACHE_DURATION, type=int,
              help='Seconds for which cache entries should exist')
@click.option('-a', '--subnet', default=DEFAULT_SUBNET, help='CIDR range of IP addresses to randomly generate')
@click.option('-d', '--db-path', default=DEFAULT_DB_PATH, help='Path to sqlite3 database')
def dns(laddr, lport, time, subnet, db_path):
    click.echo('Running Delirium DNS Server')
    s = FakeDNSServer(laddr, lport, time, subnet, db_path)
    try:
        s.start()
    except KeyboardInterrupt:
        pass
    finally:
        s.stop()


delirium.add_command(dns)


if __name__ == "__main__":
    delirium()
