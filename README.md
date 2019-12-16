# delirium

[![Build Status](https://travis-ci.org/disruptive-solutions/delirium.svg?branch=master)](https://travis-ci.org/disruptive-solutions/delirium)

Track and provide fake DNS responses and caching.  Designed to be used in a sandbox to analyze malware.

The use-case for this is to solve my problem with using INetSim in concert with Cuckoo sandbox.  Malware sometimes beacons out to a domain.  INetSim will respond to every DNS request with its IP address.  The analysis sandbox (Cuckoo in this case) captures the DNS request/answer and subsequent traffic to the INetSim address.  The problem here is that c2.malware.tld resolves to the same IP address as windowsupdate.tld making it very difficult to differentiate the rest of the traffic.

Nothing on the market solved this problem, so I wrote delirium.  With delirium, the IPs are unique for a duration of time so the relationship between FQDN and IP address can be tracked throughout the analysis session.  The IP range and cache duration are configurable.  Once Delirium is implemented, you will find it very easy to sift through the traffic and locate important traffic.  Delirium also supports reverse lookups (PTR records) for as long as the cache duration.

I recommend disabling INetSim's DNS service and replacing it with Delirium.  I then recommend setting INetSim as the default gateway of your analysis VM and implementing the below `REDIRECT` rule in `iptables`.  This will provide a better illusion of internet connectivity as requests to any IP address will be sent to INetSim (which will respond with fake content).

#### Some helpful thoughts and snippets:

I'm using a stand-alone virtual-machine to host my INetSim services along with delirium.  This stand-alone VM is also the gateway I use for all of my analysis VMs.  If you have a similar setup, you'll need to redirect traffic destined to the unique addresses to the INetSim services (you'll want them listening on `0.0.0.0` unless you want to use `DNAT`).  I've accomplished this with the following `iptables` rule:
```
iptables -t nat -A PREROUTING -i ens33 -j REDIRECT
```
The above will give the illusion that the INetSim box is a regular gateway providing connectivity to the inetnet.  In reality, the INetSim box is redirecting all requests to itself and responding with fake content.
