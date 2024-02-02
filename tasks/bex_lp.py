import logging
import random
import asyncio
import requests
from typing import Optional

from fake_useragent import UserAgent

from data.config import logger
from libs.py_eth_async.data.models import TokenAmount

from tasks.base import Base
from data.models import Tokens, Pools, Routers, Liquidity_Tokens, BaseContract


# Made by Toby LP
class BexLP(Base):
    NAME = 'BexLP'
    AVAILABLE_DEPOSIT = ['STGUSDC', 'HONEY', 'WBTC', 'WETH']
    CONTRACT_MAP = {
        'BERA': Tokens.BERA,
        'WBTC': Tokens.WBTC,
        'WETH': Tokens.WETH,
        'WBERA': Tokens.WBERA,
        'HONEY': Tokens.HONEY,
        'STGUSDC': Tokens.STGUSDC,
    }
    POOLS_MAP = {
        'WBERA_HONEY': '', #Todo Make later for Bear
        'WBTC_HONEY': Pools.WBTC_HONEY_POOL,
        'WETH_HONEY': Pools.WETH_HONEY_POOL,
        'STGUSDC_HONEY': Pools.STGUSDC_HONEY_POOL
    }

    POOLS_MAP_SPECIAL = {  # This is our tokens on balance
        'WBTC_HONEY': Liquidity_Tokens.WBTC_HONEY_POOL_SPECIAL,
        'WETH_HONEY': Liquidity_Tokens.WETH_HONEY_POOL_SPECIAL,
        'STGUSDC_HONEY': Liquidity_Tokens.STGUSDC_HONEY_POOL_SPECIAL,
    }

    async def add_liquidity(self, token: str):
        if token in self.AVAILABLE_DEPOSIT:
            try:
                token = self.CONTRACT_MAP[token]
                amount, swap_data, failed_text = await self.deposit_data_single(token)
                if amount.Wei == 0:
                    return logger.error(f'Token {token.title} balance is 0!')
                await self.tx_build(token=token, amount=amount, swap_data=swap_data,
                                                   failed_text=failed_text)
            except BaseException as e:
                logging.exception(f'BEX.wrap_bera')
                # return f'{failed_text}: {e}'
        else:
            logger.error(f'{self.client.account.address} via'
                         f"{self.NAME}  Deposit LP | can't find token: '{token}' ")
            return

    async def deposit_data_single(self, token: BaseContract):
        amount = await self.client.wallet.balance(token=token.address)
        random_pool = await self.select_random_pool(token=token)
        # print(f'{random_pool.address.lower()[2:]:0>64}')
        swap_data = (f'0x6d517aab'
          f'{random_pool.address.lower()[2:]:0>64}'  # Pool address
          f'{self.client.account.address.lower()[2:]:0>64}'  # Our address  
          f'0000000000000000000000000000000000000000000000000000000000000080'
          f'00000000000000000000000000000000000000000000000000000000000000c0'
          f'0000000000000000000000000000000000000000000000000000000000000001'
          f'{token.address.lower()[2:]:0>64}'  # Token address 
          f'0000000000000000000000000000000000000000000000000000000000000001'  
          f'{hex(amount.Wei)[2:]:0>64}')  # Token amount
        # print(swap_data)
        failed_text = (f'Failed to deposit LP {token.title} in '
                       f'{next((key for key, val in self.POOLS_MAP.items() if val == random_pool), None)} '
                       f'to via {self.NAME}')
        logger.info(f'Try {failed_text[7:]}')
        # amount.Wei = 0 # This for test
        return amount, swap_data, failed_text

    async def select_random_pool(self, token: BaseContract):
        if token.title == 'HONEY':
            keys = ['WBTC_HONEY', 'WETH_HONEY', 'STGUSDC_HONEY']
            return self.POOLS_MAP[random.choice(keys)]
        if token.title == 'WBTC':
            return self.POOLS_MAP['WBTC_HONEY']
        if token.title == 'WETH':
            return self.POOLS_MAP['WETH_HONEY']
        if token.title == 'STGUSDC':
            return self.POOLS_MAP['STGUSDC_HONEY']

    async def remove_liquidity(self, token: str):
        if token == 'WBTC_HONEY' or 'WETH_HONEY' or 'STGUSDC_HONEY':
            try:
                token = self.POOLS_MAP[token]
                amount, swap_data, failed_text = await self.withdraw_data(pool=token)
                if amount.Wei == 0:
                    return logger.error(f'Token {token.title} balance is 0!')
                token = self.POOLS_MAP_SPECIAL[token.title]
                await self.tx_build(token=token, amount=amount, swap_data=swap_data,
                                                   failed_text=failed_text)
            except BaseException as e:
                logging.exception(f'BEX_LP.error')
                # return f'{failed_text}: {e}'
        else:
            logger.error(f'{self.client.account.address} via'
                         f"{self.NAME}  Deposit LP | can't find token: '{token}' ")
            return

    async def withdraw_data(self, pool: BaseContract):
        amount = await self.client.wallet.balance(token=f'{(self.POOLS_MAP_SPECIAL[pool.title]).address}')
        swap_data = (f'0xe9942531'
          f'{pool.address.lower()[2:]:0>64}'  # Pool address
          f'{self.client.account.address.lower()[2:]:0>64}'  # Our address  
          f'{(self.POOLS_MAP_SPECIAL[pool.title]).address[2:]:0>64}'  # special for each pool address 
          f'{hex(amount.Wei)[2:]:0>64}')  # Pool amount
        failed_text = (f'Failed to withdraw LP from '
                       f'{next((key for key, val in self.POOLS_MAP.items() if val == pool), None)} '
                       f'to via {self.NAME}')
        # print(swap_data)
        # amount.Wei = 0 # This for test
        return amount, swap_data, failed_text

    async def tx_build(self, token: BaseContract, amount: TokenAmount,
                                      swap_data, failed_text, test=False):
        try:
            if test:
                print(swap_data)
            if not await self.approve_interface(
                    token_address=token.address,
                    spender=Routers.DEPOSIT_POOL_BEX.address,
                    amount=amount
            ):
                return f'{failed_text}: token not approved.'

            await asyncio.sleep(random.randint(15, 25))

            logger.info(f'{self.client.account.address} | '
                        f'{failed_text[7:]} | amount: {amount.Ether}')

            tx_params = {
                'chainId': self.client.network.chain_id,
                'nonce': await self.client.wallet.nonce(),
                'from': self.client.account.address,
                'to': Routers.DEPOSIT_POOL_BEX.address,
                'data': swap_data,
                'value': 0 if token.title != 'BERA' else amount.Wei,
            }

            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)
            # receipt, tx_hash = await self.submit_transaction(tx_params)
            if isinstance(receipt, dict):
                logger.success(f'{amount.Ether} {token.title} was added {failed_text[7:]}: {tx.hash.hex()}')
                return (f'{amount.Ether} {token.title} was added '
                        f'{failed_text[7:]}: {tx.hash.hex()}')
            return f'{failed_text} | In build_tx'

        except BaseException as e:
            logging.exception(f'{self.NAME}.deposit')
            return f'{failed_text}: {e}'
