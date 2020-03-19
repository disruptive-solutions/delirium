# delirium

## Overview
`Delirium` is an application intended to help with malware analysis in a sandbox environment by supplying services that better simulate a network.

Currently, there is only one service that has been implemented: DNS.

## DNS
Internally assigns an IP address per unique hostname queried via DNS request, and serves DNS responses based on those assignments.

The intent is for an analyst to be able to more easily spot patterns of network behavior.

 The assigned IPs are unique for a duration of time so the relationship between FQDN and IP address can be tracked throughout the analysis session.

 The IP range and record life are configurable. When a DNS record is accessed the first time, it is added to the database. Each subsequent look-up updates the expiration time of that record.

 Delirium also supports reverse lookups (PTR records) for the duration of the records life.


### Usage
```
Usage: delirium dns [OPTIONS]

Options:
  -l, --laddr TEXT     Address to listen on
  -p, --lport INTEGER  Port to listen on (UDP)
  -t, --time INTEGER   Life of records in seconds
  -s, --subnet TEXT    Subnet used to generate IP addresses
  --db-path TEXT       Path to sqlite3 database
  --delete             Delete stale entries instead of marking them
  --log-path TEXT      Path to write logs
  -v, --verbose        Set the verbosity level
  --help               Show this message and exit.
```


#### `Python:`
```python
from delirium.dns import FakeDNSServer
server = FakeDNSServer()
server.start()
```
Optional positional or keyword args:
* `listen_addr`
* `listen_port`

Optional keyword-only args:
* `record_life` - `int` default: 900 seconds (15 minutse)
* `subnet` - `str` default: '10.0.0.0/24'
* `db_path` - `str` default: ':memory:'
* `remove_records` - `bool` default: `False`
* `logger` - `DeliriumDNSLogger` default: `None`


### Examples
#### Run with Defaults
```
delirium dns
```
This runs `delirium dns` with its default settings.

This means:
-  Records database is stored in `memory` (non-persistent)
-  Stale records are NOT deleted from the database
-  Listens for DNS queries on `0.0.0.0:53`
-  Cache entries are kept alive for `900s`
-  Addresses are assigned from the `10.0.0.0/24` range

#### Persistent database
```
delirium dns --db-path /path/to/db.sqlite
```
This runs `delirium dns` with a persistent database stored on disk at `/path/to/db.sqlite`

#### Subnet must be at least a /30
```
delirium dns --subnet 10.0.0.1/32
```
This will cause the `delirium dns` to fail due to there being too small of an address pool.

## Notes on implementation:

I'm using a stand-alone virtual-machine to host my INetSim services along with Delirium.  This stand-alone VM is also the gateway I use for all of my analysis VMs.  I recommend disabling INetSim's DNS service and replacing it with Delirium.  I then recommend setting INetSim as the default gateway of your analysis VM and implementing the below `REDIRECT` rule in `iptables`.  This will provide a better illusion of internet connectivity as requests to any IP address will be sent to INetSim (which will respond with fake content).  If you have a similar setup, you'll need to redirect traffic destined to the unique addresses to the INetSim services (you'll want them listening on `0.0.0.0` unless you want to use `DNAT`).  I've accomplished this with the following `iptables` rule:
```
iptables -t nat -A PREROUTING -i ens33 -j REDIRECT
```
The above will give the illusion that the INetSim box is a regular gateway providing connectivity to the internet.  In reality, the INetSim box is redirecting all requests to `127.0.0.1` and responding with fake content.

### Database location
The default location for `delirium` is in memory. This means that the associations between hostnames and IP addresses will only persist in logs unless the `--db-path` is set to a file on disk.

### Logging
Logging is output to `stderr` alone by default. A log file location can be specified using the `--log-name` switch. The log will at 500KB and three backups will be kept.
