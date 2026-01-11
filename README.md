# Zerion API Library / CLI Tool

<p>A tool to query https://zerion.io's API. Notice: this is an alpha release 
WIP.</p>

#### Usage

<pre>
usage: main.py [-h] [-r] {gas,chains,wallet} ...

Zerion API Client

positional arguments:
  {gas,chains,wallet}

options:
  -h, --help           show this help message and exit
  -r, --raw            Do not pretty print, for piping to jq
</pre>

##### Get assets in wallet

<pre>
usage: main.py wallet [-h] address

positional arguments:
  address

options:
  -h, --help  show this help message and exit
</pre>

##### TODO

- add functions for the rest of the endpoints (see https://zerion.io/api)
- create a pip-installable package that supports `-m` style invocation