# Breakwater-artifact

This repository includes Breakwater and applications that
were evaluated in Breakwater (OSDI '20).

## Quick Start (Cloudlab xl170)
The easiest way to reproduce the paper result is using Cloudlab xl170 cluster. You can find a pre-configured disk image with `urn:publicid:IDN+utah.cloudlab.us+image+creditrpc-PG0:breakwater-xl170-2`. The Cloudlab profile for the same experiment environment (11 xl170 machines are connected to a single switch) as the paper can be found [here](https://www.cloudlab.us/p/CreditRPC/breakwater-compact/0).

1. Initialize submodules
```
$ ./init_submodules.sh
```

2. Provide the information on remote servers in `config_remote.py`.

3. Set up remote environment
```
$ ./setup_remote_xl170.py
```

4. Start experiment script

For a synthetic experiment:
```
$ ./run_synthetic.py
```
For a Memcached experiment:
```
$ ./run_memcached.py
```
