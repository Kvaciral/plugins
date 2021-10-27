# Http Invoice Request Server plugin


This plugin starts a minimal, rate limited HTTP Server and returns a invoice on the following GET request:

``/payRequest?amount=...``

```
$ curl http://localhost:8806/payRequest?amount=123123
{"pr":"lnbc123123...","routes":[]}
```

The webserver is rate-limited, meaning that only a certain amount of request per minute is allowed (to prevent DoS attacks).

The json invoice can be used by other services, for example a service for tipping, donations, PoS devices, ...

##### Onion routing
Exposing the url using Onion routing is easy. Install tor and 
add the service to `/etc/tor/torrc`
```
HiddenServiceDir /home/bitcoin/tor/request-invoice-service_v2/
HiddenServicePort 80 127.0.0.1:8806

```
and restart tor to create the url
```
$ systemctl stop tor && systemctl start tor
$ cat /home/bitcoin/tor/request-invoice-service_v2/hostname
fkfuvjrbj6cfqppq6xcgfwmp4p23wq2unzlnqmdi6ibqtg2aq7thp2qd.onion
```

Use tor browser to visit the url and create a invoice (and make a donation?).
http://fkfuvjrbj6cfqppq6xcgfwmp4p23wq2unzlnqmdi6ibqtg2aq7thp2qd.onion/invoice/1000/donation

##### Configuration
You can enter the path to the webserver's JSON-file (/home/www/host/.well-knwon/lnurlp/jsonfile) for metadata-extraction:

- `--lnurlp-meta-path=...`

(optional) You can initialize the plugin with a specific port and address:

- `--lnurlp-address=... (default 127.0.0.1)`
- `--lnurlp-port=... (default 8806)`
