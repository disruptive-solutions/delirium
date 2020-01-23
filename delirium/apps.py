import click

from . import const
from .dns import FakeDNSServer


@click.group()
def delirium():
    pass


@click.command()
@click.option('-l', '--laddr', default=const.DEFAULT_LISTEN_ADDR, help='Address to listen on')
@click.option('-p', '--lport', default=const.DEFAULT_LISTEN_PORT, type=int, help='Port to listen on (UDP)')
@click.option('-t', '--time', default=const.DEFAULT_CACHE_DURATION, type=int,
              help='Seconds for which cache entries should exist')
@click.option('-a', '--subnet', default=const.DEFAULT_SUBNET, help='CIDR range of IP addresses to randomly generate')
@click.option('-d', '--db-path', default=const.DEFAULT_DB_PATH, help='Path to sqlite3 database')
def dns(laddr, lport, time, subnet, db_path):
    click.echo('Running Delirium DNS Server')
    server = FakeDNSServer(laddr, lport, time, subnet, db_path)
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


delirium.add_command(dns)


if __name__ == "__main__":
    delirium()
