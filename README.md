# Breakwater-artifact

This repository includes Breakwater and applications that
were evaluated in Breakwater (OSDI '20).

## Quick Start (Cloudlab XL170)
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
