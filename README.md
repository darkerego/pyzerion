# Zerion API Library / CLI Tool

<p>A tool to query https://zerion.io's API. Notice: this is an alpha release 
WIP.</p>

#### Usage

<pre>
usage: main.py [-h] [-r] {gas,chains,wallet,file} ...

Zerion API Client

positional arguments:
  {gas,chains,wallet,file}
    gas                 Get gas prices and information for all supported chains
    chains              Get all supported chains
    wallet              Scan a single ethereum wallet for balance data
    file                Scan multiple addresses from file

options:
  -h, --help            show this help message and exit
  -r, --raw             Do not pretty print, for piping to jq
</pre>

##### Get assets in wallet

<pre>
usage: main.py wallet [-h] address

positional arguments:
  address

options:
  -h, --help  show this help message and exit
</pre>


##### Get assets in a list of wallets

<pre>
usage: main.py file [-h] [--delay DELAY] path

positional arguments:
  path           Path to list of addresses

options:
  -h, --help     show this help message and exit
  --delay DELAY  Delay between requests
</pre>

<p>
Note: adjust the delay in between requests to suit your key's rate limit 
<br>
Example: `--delay 0.5`
</p>

##### TODO:

- add functions for the rest of the endpoints (see https://zerion.io/api)
- create a pip-installable package that supports `-m` style invocation