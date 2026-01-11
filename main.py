#!/usr/bin/env python3
####################################################
# Zerion API Command Line Tool / Library ~ Copyright DarkerEgo ~ 2026
# https://github.com/darkerego
####################################################

import argparse
import asyncio
import base64
import json
from os import environ
from pprint import pprint
from typing import Any, Dict, List, Optional, Coroutine

import httpx
import web3
from dotenv import load_dotenv
from eth_typing import ChecksumAddress


class EnvironmentNotConfigured(Exception):
    pass

"""
* Library for interacting with https://zerion.io's API -- primarily for wallet appraisal / valuation
* Notice: this is an alpha release W.I.P.
"""

class ZerionApi:
    def __init__(self, _api_key: str = None):
        load_dotenv()
        self.api_key = _api_key if _api_key else environ.get('ZERION_API_KEY')
        self.encoded_api_key = base64.b64encode(self.api_key.encode()+b':').decode()
        self.headers = {'Authorization': 'Basic %s' % self.encoded_api_key,"accept": "application/json"}
        self.session = httpx.AsyncClient()
        self.chain_list: list[str] = []

    """
    Checks if __a_init__ has ran yet by checking if the program has retrieved 
    the list of supported chains from the API.
    @:return bool
    """
    @property
    def initialized(self):
        if len(self.chain_list) > 0:
            return True
        return False

    """
    Load list of supported chains into memory
    """
    async def __a_init__(self):
        await self.chains()

    """
    HTTP get function
    @:param url: full url to get
    @:param params: URL query parameters, if any
    """

    async def _get(self, url: str, params: dict = None) -> dict:
        if not params:
            params = {}
        response = await self.session.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    """
    HTTP post function
    @:param url: full url to post
    @:param params: POST query parameters, if any
    @:return dict
    """

    async def _post(self, url: str, data: dict = None) -> dict:
        if not data:
            data = {}
        response = await self.session.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return await response.json()

    """
    Parses returned portfolio data into human readable format
    @:param portfolio_json: json data returned from API's /wallet/positions endpoint
    @:return dict
    """

    @staticmethod
    async def parse_wallet_positions(portfolio_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        data = portfolio_json.get("data", [])

        for position in data:
            attributes = position.get("attributes", {})
            relationships = position.get("relationships", {})
            value_usd = attributes.get("value")
            # Skip negative or missing values
            if value_usd is None or value_usd < 0:
                continue

            quantity = attributes.get("quantity", {})
            amount = quantity.get("float")
            decimals = quantity.get("decimals", 0)
            price = attributes.get("price")
            day_change = attributes.get('changes').get("percent_1d")
            if float(day_change) > 0:
                day_change_human = str("+" + str(round(float(day_change), 4)) + "%")
            else:
                day_change_human = str(round(float(day_change), 4)) + "%"

            fungible_info = attributes.get("fungible_info", {})
            asset_name = fungible_info.get("name")
            asset_symbol = fungible_info.get("symbol")
            # Determine chain ID from relationships
            chain_data = relationships.get("chain", {}).get("data", {})
            chain_id = chain_data.get("id")
            # Resolve contract address for the correct chain
            contract_address: Optional[str] = None
            implementations = fungible_info.get("implementations", [])
            for impl in implementations:
                if impl.get("chain_id") == chain_id:
                    contract_address = impl.get("address")
                    break

            # Fallback: if no exact chain match, use the first implementation
            if contract_address is None and implementations:
                contract_address = implementations[0].get("address")
                if contract_address is None:
                    contract_address = '0x' + '0' * 40

            asset_entry = {
                "name": asset_name,
                "symbol": asset_symbol,
                "chain": chain_id,
                "decimals": decimals,
                "contract_address": contract_address,
                "amount": amount,
                "value_usd": value_usd,
                "price": price,
                "1d_change_str": day_change_human,
                "1d_change_flt": day_change,
            }
            results.append(asset_entry)
        return results

    """
    Get current gas price information for all supported chains
    @:return dict
    """

    async def gas(self) -> dict:
        return await self._get(url="https://api.zerion.io/v1/gas-prices/")

    """
    Get a list of all supported chains / extract the chain names and store in memory at program start
    @:return dict
    """
    async def chains(self) -> dict:
        _ret = await self._get(url="https://api.zerion.io/v1/chains/")
        if not self.initialized:
            for c in _ret.get('data'):
                self.chain_list.append(c.get('id'))
        return _ret

    """
    @:param address: a 0x style Ethereum address
    @:return dict
    """

    async def _wallet(self, address: ChecksumAddress | str) -> dict:
        if not self.initialized:
            await self.__a_init__()
        url = "https://api.zerion.io/v1/wallets/%s/positions/?filter[positions]=no_filter&currency=usd&filter" \
               "[trash]=only_non_trash&sort=value&sync=false" % address.__str__()
        return await self._get(url=url)

    async def wallet(self, address: ChecksumAddress | str) -> list[dict[str, Any]]:
        results = await self._wallet(address)
        return await self.parse_wallet_positions(results)

"""
Command line tool entry point
"""

def main():
    parser = argparse.ArgumentParser(description='Zerion API Client')
    parser.add_argument('-r', '--raw', action='store_true', help='Do not pretty print, '
                                                                 'for piping to jq')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('gas')
    subparsers.add_parser('chains')
    wallet = subparsers.add_parser('wallet')
    wallet.add_argument('address', type=str)
    args = parser.parse_args()
    load_dotenv()
    api_key = environ.get('ZERION_API_KEY', False)
    if not isinstance(api_key, str):
        raise EnvironmentNotConfigured("dotenv variable `ZERION_API_KEY` is not set!")
    api = ZerionApi(api_key)
    if args.command == 'wallet':
        coro = api.wallet(web3.Web3.to_checksum_address(args.address))
    else:
        fn = getattr(api, args.command)
        coro = fn()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    ret = loop.run_until_complete(coro)
    if args.raw:
        print(json.dumps(ret))
    else:
        pprint(ret)

if __name__ == "__main__":
    main()

