import click
import logging

from ipaddress import IPv4Network

from delirium import const
from delirium.dns import FakeDNSServer, DeliriumDNSLogger


verbose_levels = (logging.WARNING, logging.INFO, logging.DEBUG)
verbose_opt_type = click.IntRange(0, len(verbose_levels)-1, clamp=True)


@click.group()
def delirium():
    pass


@click.command()
@click.option('-l', '--laddr', default=const.DEFAULT_LISTEN_ADDR,
              help='Address to listen on')
@click.option('-p', '--lport', default=const.DEFAULT_LISTEN_PORT, type=int,
              help='Port to listen on (UDP)')
@click.option('-t', '--time', default=const.DEFAULT_CACHE_DURATION, type=int,
              help='Life of records in seconds')
@click.option('-s', '--subnet', default=const.DEFAULT_SUBNET,
              help='Subnet used to generate IP addresses')
@click.option('--db-path', default=const.DEFAULT_DB_URI,
              help='Path to sqlite3 database')
@click.option('--delete', default=False, is_flag=True,
              help='Delete stale entries instead of marking them')
@click.option('--log-path', default=None,
              help='Path to write logs')
@click.option('-v', '--verbose', default=0, count=True, type=verbose_opt_type,
              help='Set the verbosity level')
def dns(laddr, lport, time, subnet, db_path, delete, log_path, verbose):
    level = verbose_levels[verbose]
    logger = DeliriumDNSLogger(level=level, path=log_path)

    if IPv4Network(subnet).prefixlen > 30:
        logger.critical('Address pool too small - CIDR must be 30 or larger')
        return
    if IPv4Network(subnet).prefixlen > 24:
        logger.warning('Using a subnet smaller than /24 is not recommended')
    elif IPv4Network(subnet).prefixlen <= 16:
        logger.warning('Using a subnet larger than /16 may impact performance')

    server = FakeDNSServer(laddr, lport,
                           subnet=subnet,
                           db_path=db_path,
                           record_life=time,
                           remove_records=delete,
                           logger=logger)
    try:
        server.start()
    except KeyboardInterrupt:
        logger.debug('Keyboard interrupt')
    finally:
        server.stop()


delirium.add_command(dns)


if __name__ == "__main__":
    delirium(auto_envvar_prefix='DELIRIUM')  # pylint: disable=unexpected-keyword-arg
