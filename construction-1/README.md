### Requirement: python3 python-crypto

### Set up tracker:
#### python3 btserver0.py tracker-host tracker-port max-peers default-ip:port
    $ python3 btserver0.py 127.0.0.1 7090 0 0.0.0.0:8090

### Set up 2^(N+1) - 1 nodes:
    $ python3 auto.py N

### Client requests to upload/fetch blocks:
#### python btclient1.py -c 1 peer-host peer-port max-peers tracker-ip:port"
    $ python3 btclient2.py -c 1 127.0.0.1 20000 0 127.0.0.1:7090

### Stop running nodes (kill all running python processes):
    $ python kill.py
