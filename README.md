# fake_dns

[![Build Status](https://travis-ci.org/disruptive-solutions/fake_dns.svg?branch=master)](https://travis-ci.org/disruptive-solutions/fake_dns)

Provide fake and random DNS responses in a sandbox.

The use-case for this is to solve my problem with Cuckoo.  That malware beacons out to some domain and I capture the DNS request.  But, Cuckoo doesn't know about this transaction and has no way of cataloguing the traffic.  As part of post-processing Cuckoo does some reverse DNS lookups on IPs that the malware attempts to beacon out to.  Nothing on the market solved this problem.  So, I wrote something that does.  INetSim and similar respond to everything with one single IP.  This makes it difficult to differentiate between malware.tld and legit-site.com after the initial DNS requests.  With this, the IPs are unique so they can be tracked throughout the analysis session
