import random

import asyncio
import logging

from decimal import Decimal
from web3 import Web3
from typing import Optional
from web3.middleware import geth_poa_middleware

from libs.py_eth_async.client import Client
from aiohttp_proxy import ProxyConnector
from libs.pretty_utils.type_functions.floats import randfloat
from libs.py_eth_async.data.models import TxArgs, Ether, Wei, Unit

from data.config import logger
from data.models import SwapInfo

from data.models import BaseContract

from data.models import (
    Settings,
    TokenAmount,
    Tokens,
    Liquidity_Tokens,
    Lending_Tokens,
    Ether,
)

settings = Settings()

class Base:
    def __init__(self, client: Client):
        self.client = client

    async def get_decimals(self, contract_address: str) -> int:
        contract = await self.client.contracts.default_token(contract_address=contract_address)
        return await contract.functions.decimals().call()

    def get_random_amount(self):
        settings = Settings()
        return Ether(randfloat(
            from_=settings.eth_amount_for_swap.from_,
            to_=settings.eth_amount_for_swap.to_,
            step=0.0000001
        ))

    async def check_balance_insufficient(self, amount):
        """returns if balance does not have enough token"""
        balance = await self.client.wallet.balance()
        # if balance < amount + settings.minimal_balance:
        if balance.Ether < amount.Ether:
            return True
        return False

    async def submit_transaction(self, tx_params, test=False):
        gas = await self.client.transactions.estimate_gas(w3=self.client.w3, tx_params=tx_params)

        tx_params['gas'] = gas.Wei

        if test:
            print(tx_params['data'])
            return "test", "test"
        else:
            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            return await tx.wait_for_receipt(client=self.client, timeout=300), tx.hash.hex()

    async def base_swap_eth_to_token(
            self,
            swap_data,
            amount,
            swap_info: SwapInfo,
            tx_paramam_have=False,
            test=False
    ):
        failed_text = (f'Failed to swap {swap_info.token_from.title}'
                       f'to {swap_info.token_to.title} via {swap_info.swap_platform.title}')

        try:
            if test:
                print(swap_data)

            if await self.check_balance_insufficient(amount):
                logger.error(
                    f'{self.client.account.address} | {swap_info.swap_platform.title} '
                    f'| swap_eth | insufficient eth balance')

                return f'{failed_text}: insufficient balance.'

            logger.info(
                f'{self.client.account.address} | {swap_info.swap_platform.title} | swap_eth | amount: {amount.Ether}')

            if tx_paramam_have:
                tx_params = swap_data
            else:
                gas_price = await self.client.transactions.gas_price(w3=self.client.w3)

                tx_params = {
                    'gasPrice': gas_price.Wei,
                    'from': self.client.account.address,
                    'to': swap_info.swap_platform.address,
                    'data': swap_data,
                    'value': amount.Wei
                }

            receipt, tx_hash = await self.submit_transaction(tx_params)
            if receipt:
                return (f'{amount.Ether} {swap_info.token_from.title} was swapped to '
                        f'{swap_info.token_to.title} via {swap_info.swap_platform.title}: {tx_hash}')

            return (f'Failed to swap {swap_info.token_from.title}'
                    f' to {swap_info.token_to.title} via {swap_info.swap_platform.title}')

        except BaseException as e:
            logging.exception(f'{swap_info.swap_platform}.swap_eth')
            return f'{failed_text}: {e}'

    async def base_swap_token_to_eth(
            self,
            tx_contract,
            swap_data,
            swap_info: SwapInfo,
            tx_paramam_have=False,
            test=False
    ) -> str:
        failed_text = (f'Failed to swap {swap_info.token_from.title}'
                       f' to {swap_info.token_to.title} via {swap_info.swap_platform.title}')

        try:
            if test:
                print(swap_data)
            token_balance = await self.client.wallet.balance(token=swap_info.token_from.address)

            if not token_balance.Wei:
                logger.error(
                    f'{self.client.account.address} |'
                    f' {swap_info.swap_platform.title} | swap_token | insufficient token balance')

                return f'{failed_text}: insufficient balance.'
            logger.info(
                f'{self.client.account.address} | {swap_info.swap_platform.title}'
                f' | swap_token | amount: {token_balance.Ether}')

            if not await self.approve_interface(
                    token_address=swap_info.token_from.address,
                    spender=tx_contract.address,
                    amount=token_balance
            ):
                return f'{failed_text}: token not approved.'

            await asyncio.sleep(random.randint(10, 20))
            if tx_paramam_have:
                tx_params = swap_data
            else:
                gas_price = await self.client.transactions.gas_price(w3=self.client.w3)

                tx_params = {
                    'gasPrice': gas_price.Wei,
                    'from': self.client.account.address,
                    'to': tx_contract.address,
                    'data': swap_data
                }

            receipt, tx_hash = await self.submit_transaction(tx_params)

            if receipt:
                return (f'{token_balance.Ether} {swap_info.token_from.title}'
                        f' was swapped to {swap_info.token_to.title} via {swap_info.swap_platform.title}: {tx_hash}')

            return (f'Failed to swap {swap_info.token_from.title}'
                    f' to {swap_info.token_to.title} via {swap_info.swap_platform.title}')

        except BaseException as e:
            logging.exception(f'{swap_info.swap_platform.title}.swap_token')
            return f'{failed_text}: {e}'

    async def eth_to_weth(self, amount: TokenAmount) -> str:
        failed_text = 'Failed to wrap ETH'

        try:
            logger.info(f'{self.client.account.address} | eth -> weth')
            contract = await self.client.contracts.get(contract_address=Tokens.WETH)
            settings = Settings()
            if not amount:
                amount = Ether(randfloat(
                    from_=settings.eth_amount_for_swap.from_,
                    to_=settings.eth_amount_for_swap.to_,
                    step=0.0000001
                ))

            balance = await self.client.wallet.balance()

            if float(balance.Ether) < float(amount.Ether) + settings.minimal_balance:
                logger.error(f'{self.client.account.address} | Base | eth_to_weth | insufficient eth balance')
                return f'{failed_text}: insufficient balance.'

            gas_price = await self.client.transactions.gas_price(w3=self.client.w3)

            tx_params = {
                'gasPrice': gas_price.Wei,
                'from': self.client.account.address,
                'to': contract.address,
                'data': contract.encodeABI('deposit'),
                'value': amount.Wei
            }
            gas_limit = await self.client.transactions.estimate_gas(w3=self.client.w3, tx_params=tx_params)
            tx_params['gas'] = gas_limit.Wei
            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

            if receipt:
                return f'ETH was wrapped: {tx.hash.hex()}'

            return f'{failed_text}!'

        except BaseException as e:
            logging.exception('Base.eth_to_weth')
            return f'{failed_text}: {e}'

    async def weth_to_eth(self) -> str:
        failed_text = 'Failed to unwrap ETH'

        try:
            logger.info(f'{self.client.account.address} | weth -> eth')
            weth_balance = await self.client.wallet.balance(token=Tokens.WETH)

            if not weth_balance.Wei:
                logger.error(f'{self.client.account.address} | Base | weth_to_eth | insufficient weth balance')
                return f'{failed_text}: insufficient balance.'

            contract = await self.client.contracts.get(contract_address=Tokens.WETH)
            args = TxArgs(
                wad=weth_balance.Wei
            )
            gas_price = await self.client.transactions.gas_price(w3=self.client.w3)
            tx_params = {
                'from': self.client.account.address,
                'to': contract.address,
                'data': contract.encodeABI('withdraw', args=args.tuple()),
            }

            gas_limit = await self.client.transactions.estimate_gas(w3=self.client.w3, tx_params=tx_params)
            tx_params['gas'] = gas_limit.Wei
            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

            if receipt:
                return f'ETH was unwrapped: {tx.hash.hex()}'

            return f'{failed_text}!'

        except BaseException as e:
            logging.exception('Base.weth_to_eth')
            return f'{failed_text}: {e}'

    async def approve_interface(self, token_address, spender, amount: Optional[TokenAmount] = None) -> bool:
        logger.info(
            f'{self.client.account.address} | start approve token_address: {token_address} for spender: {spender}'
        )
        balance = await self.client.wallet.balance(token=token_address)

        if balance <= 0:
            logger.error(f'{self.client.account.address} | approve | zero balance')
            return False

        if not amount or amount.Wei > balance.Wei:
            amount = balance

        approved = await self.client.transactions.approved_amount(
            token=token_address,
            spender=spender,
            owner=self.client.account.address
        )

        if amount.Wei <= approved.Wei:
            logger.info(f'{self.client.account.address} | approve | already approved')
            return True

        tx = await self.client.transactions.approve(
            token=token_address,
            spender=spender,
            amount=amount,
        )
        receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

        if receipt:
            return True

        return False

    @staticmethod
    async def get_max_priority_fee_per_gas(w3: Web3, block: dict) -> int:
        block_number = block['number']
        latest_block_transaction_count = w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_lst = []

        for i in range(latest_block_transaction_count):
            try:
                transaction = w3.eth.get_transaction_by_block(block_number, i)
                if 'maxPriorityFeePerGas' in transaction:
                    max_priority_fee_per_gas_lst.append(transaction['maxPriorityFeePerGas'])

            except Exception:
                continue

        if not max_priority_fee_per_gas_lst:
            max_priority_fee_per_gas = w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_lst.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_lst[len(max_priority_fee_per_gas_lst) // 2]

        return max_priority_fee_per_gas

    @staticmethod
    async def get_base_fee(w3: Web3, increase_gas: float = 1.):
        last_block = await w3.eth.get_block('latest')
        return int(last_block['baseFeePerGas'] * increase_gas)

    @staticmethod
    async def get_max_fee_per_gas(w3: Web3, max_priority_fee_per_gas: Unit) -> Wei:
        base_fee = await Base.get_base_fee(w3=w3)
        # print('base_fee', base_fee)
        return Wei(base_fee + max_priority_fee_per_gas.Wei)

    @staticmethod
    async def send_transaction(
            client: Client,
            private_key: str,
            to: str,
            data,
            from_=None,
            increase_gas=1.1,
            value=None,
            max_priority_fee_per_gas: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None
    ):
        if not from_:
            from_ = client.account.address

        tx_params = {
            'chainId': await client.w3.eth.chain_id,
            'nonce': await client.w3.eth.get_transaction_count(client.account.address),
            'from': Web3.to_checksum_address(from_),
            'to': Web3.to_checksum_address(to),
            'data': data,
        }

        if client.network.tx_type == 2:
            w3 = Web3(provider=Web3.HTTPProvider(endpoint_uri=client.network.rpc))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            last_block = w3.eth.get_block('latest')

            if not max_priority_fee_per_gas:
                max_priority_fee_per_gas = await Base.get_max_priority_fee_per_gas(w3=w3, block=last_block)

            if not max_fee_per_gas:
                base_fee = int(last_block['baseFeePerGas'] * 1.125)
                max_fee_per_gas = base_fee + max_priority_fee_per_gas
            tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            tx_params['maxFeePerGas'] = max_fee_per_gas

        else:
            tx_params['gasPrice'] = await client.w3.eth.gas_price

        if value:
            tx_params['value'] = value

        try:
            tx_params['gas'] = int(await client.w3.eth.estimate_gas(tx_params) * increase_gas)
        except Exception as err:
            logger.error(
                f'{client.account.address} | Transaction failed | {err}')
            return None

        sign = client.w3.eth.account.sign_transaction(tx_params, private_key)
        return await client.w3.eth.send_raw_transaction(sign.rawTransaction)

    def get_session(self):
        if self.client.proxy:
            return ProxyConnector.from_url(self.client.proxy)
        return None

    async def get_multiple_balances(self, token_list: list[BaseContract], max_concurrent_tasks: int = 10):
        semaphore = asyncio.Semaphore(max_concurrent_tasks)
        results = {}

        async def fetch_balance(token):
            async with semaphore:
                if token.title == 'BERA':  # or token.title == 'WBERA':
                    return
                bal = await self.client.wallet.balance(token.address)
                if bal.Ether!=0:
                    # print(f'I got balance of {token.title} - {token.address}: {bal.Ether}')
                    results[token] = bal.Ether
        tasks = [fetch_balance(token) for token in token_list]
        await asyncio.gather(*tasks)

        return results

    async def get_all_tokens(self) -> tuple[dict, dict, dict]:
        tokens = await self.get_multiple_balances(Tokens.get_token_list())
        lending_tokens = await self.get_multiple_balances(Lending_Tokens.get_token_list())
        lp = await self.get_multiple_balances(Liquidity_Tokens.get_token_list())
        return tokens, lending_tokens, lp

