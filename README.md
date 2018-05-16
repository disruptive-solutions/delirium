# delirium

[![Build Status](https://travis-ci.org/disruptive-solutions/delirium.svg?branch=master)](https://travis-ci.org/disruptive-solutions/delirium)

Track and provide fake DNS responses and caching.  Designed to be used in a sandbox to analyze malware.

The use-case for this is to solve my problem with Cuckoo.  That malware beacons out to some domain and I capture the DNS request.  But Cuckoo doesn't know about this transaction and has no way of cataloguing the traffic.  As part of post-processing Cuckoo (optionally) does some reverse DNS lookups on IPs it saw during analysis.  This is somewhat useless in a sterile sandbox as there is no real DNS solution. 

Nothing on the market solved this problem so I wrote delirium.  INetSim and similar respond to everything with one single IP.  This makes it difficult to differentiate between malware.tld and legit-site.com after the initial DNS requests (in the pcap).  With delirium, the IPs are unique for a duration of time so the relationship between real name and unique fake address can be tracked throughout the analysis session.

#### Some helpful thoughts and snippets:

I'm using a stand-alone virtual-machine to host my INetSim services along with delirium.  This stand-alone VM is also the gateway I use for all of my analysis VMs.  If you have a similar setup, you'll need to redirect traffic destined to the unique addresses to the INetSim services (you'll want them listening on something other than `127.0.0.1`).  I've accomplished this with `iptables`:
```
iptables -t nat -A PREROUTING -i ens33 -j REDIRECT
```
The above will give the illusion that the INetSim box is a regular gateway providing connectivity to the inetnet.  In reality, the INetSim box is acting as a gateway/proxy to itself.
