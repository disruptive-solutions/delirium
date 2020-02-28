import click

from ipaddress import IPv4Network

from delirium import const
from delirium.dns import FakeDNSServer


@click.group()
def delirium():
    pass


@click.command()
@click.option('-l', '--laddr', default=const.DEFAULT_LISTEN_ADDR, help='Address to listen on')
@click.option('-p', '--lport', default=const.DEFAULT_LISTEN_PORT, type=int, help='Port to listen on (UDP)')
@click.option('-t', '--time', default=const.DEFAULT_CACHE_DURATION, type=int,
              help='Seconds for which cache entries should exist')
@click.option('-s', '--subnet', default=const.DEFAULT_SUBNET, help='CIDR range of IP addresses to randomly generate')
@click.option('--db-path', default=const.DEFAULT_DB_URI, help='Path to sqlite3 database')
@click.option('--delete', default=False, is_flag=True, help='Delete stale entries from db instead of marking them')
def dns(laddr, lport, time, subnet, db_path, delete):
    if IPv4Network(subnet).prefixlen > 24 and not IPv4Network(subnet).prefixlen == 32:
        click.echo("\nCAUTION: Using a subnet smaller than /24 is not recommended due to address depletion.\n")
    elif IPv4Network(subnet).prefixlen > 30:
        click.echo("\nEXITING: Address pool too small.  CIDR must be 30 or smaller.\n")
        return
    elif IPv4Network(subnet).prefixlen <= 16:
        click.echo("\nCAUTION: Using a subnet larger than /16 may impact performance.\n")
    click.echo('Running Delirium DNS Server')

    server = FakeDNSServer(laddr, lport, time, subnet, db_path, delete)
    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


delirium.add_command(dns)


if __name__ == "__main__":
    delirium(auto_envvar_prefix='DELIRIUM')  # pylint: disable=unexpected-keyword-arg
