import random
import logging
import asyncio
from typing import Optional

from data.config import logger
from libs.py_eth_async.data.models import TokenAmount

from tasks.base import Base
from data.models import SwapInfo, Tokens, Routers, BaseContract, Lending_Tokens


# Made by Alex Lending https://artio.bend.berachain.com/dashboard
class BEND(Base):
    NAME = 'BEND'
    AVAILABLE_DEPOSIT = ['HONEY', 'WBTC', 'WETH']
    CONTRACT_MAP = {
        'WBTC': Tokens.WBTC,
        'WETH': Tokens.WETH,
        'HONEY': Tokens.HONEY,
    }
    LENDING_MAP = {
        'aWBTC': Lending_Tokens.aWBTC,
        'aWETH': Lending_Tokens.aWETH,
        'aHONEY': Lending_Tokens.aHONEY,
    }

    async def prepare_data(self, token_to_lend, balance, flag, lend_token: str = None):
        if flag:
            swap_data = (f'0x617ba037'
                         f'{token_to_lend.address[2:].zfill(64)}'
                         f'{hex(int(balance.Wei * 0.3))[2:].zfill(64)}'
                         f'{self.client.account.address[2:].zfill(64)}'
                         f'0000000000000000000000000000000000000000000000000000000000000000'
                         )
            return swap_data
        else:
            swap_data = (f'0x69328dec'
                         f'{BEND.LENDING_MAP[lend_token].address[2:].zfill(64)}'
                         f'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
                         f'{self.client.account.address[2:].zfill(64)}'
                         )
            return swap_data

    async def send_lend_tx(
            self,
            swap_data,
            swap_info: SwapInfo,
            flag,
            token_to_lend_with: Optional[BaseContract] = None,
            balance: Optional[TokenAmount] = None,
            test=False,

    ):
        failed_text = f'Failed lend/withdraw {token_to_lend_with.title} via {swap_info.swap_platform.title}'

        try:
            if test:
                print(swap_data)

            if token_to_lend_with.title in ('HONEY', 'WBTC', 'WETH'):
                if not balance.Ether:
                    logger.error(f'{self.client.account.address} |'
                                 f'{swap_info.swap_platform.title} | lend | insufficient HONEY balance')
                    return f'{failed_text}: insufficient balance.'
            if flag:
                logger.info(f'{self.client.account.address} | {swap_info.swap_platform.title} | lend | '
                            f'{token_to_lend_with.title} amount: {float(balance.Ether) * 0.3}')

                if not await self.approve_interface(
                        token_address=token_to_lend_with.address,
                        spender=Routers.BEND.address,
                        amount=balance
                ):
                    return f'{failed_text}: token not approved.'

                await asyncio.sleep(random.randint(10, 20))

            tx_params = {
                'chainId': self.client.network.chain_id,
                'nonce': await self.client.wallet.nonce(),
                'from': self.client.account.address,
                'to': swap_info.swap_platform.address,
                'data': swap_data,
            }

            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)
            # receipt, tx_hash = await self.submit_transaction(tx_params)
            if flag:
                if receipt:
                    return (f'{swap_info.token_to.title} was lent'
                            f' via {swap_info.swap_platform.title}: {tx.hash.hex()}')
                return f'Failed to lend via {swap_info.swap_platform.title}'
            else:
                if receipt:
                    return (f'{swap_info.token_to.title} was full balance withdrawn'
                            f' via {swap_info.swap_platform.title}: {tx.hash.hex()}')
                return f'Failed to lend via {swap_info.swap_platform.title}'

        except BaseException as e:
            logging.exception(f'{swap_info.swap_platform}.lend')
            return f'{failed_text}: {e}'

    async def lend(self, token_to_lend) -> str:
        token_to_lend = BEND.CONTRACT_MAP[token_to_lend]
        balance = await self.client.wallet.balance(
            token=token_to_lend.address
        )

        swap_info = SwapInfo(
            token_to_lend,
            token_to_lend,
            Routers.BEND
        )

        failed_text = f'Failed to lend {token_to_lend.title}  via {swap_info.swap_platform.title}'

        try:
            swap_data = await self.prepare_data(token_to_lend, balance, flag=True)

            return await self.send_lend_tx(
                token_to_lend_with=token_to_lend,
                swap_data=swap_data,
                swap_info=swap_info,
                balance=balance,
                flag=True
            )

        except BaseException as e:
            logging.exception(f'Bend.lend/withdraw')
            return f'{failed_text}: {e}'

    async def withdraw(self, token_to_withdraw) -> str:
        token_to_withdraw = BEND.CONTRACT_MAP[token_to_withdraw]
        lend_token = 'a' + token_to_withdraw.title
        balance = await self.client.wallet.balance(
            token=token_to_withdraw.address
        )

        swap_info = SwapInfo(
            token_to_withdraw,
            token_to_withdraw,
            Routers.BEND
        )

        failed_text = f'Failed to lend {token_to_withdraw.title}  via {swap_info.swap_platform.title}'

        try:
            swap_data = await self.prepare_data(token_to_withdraw, balance, flag=False, lend_token=lend_token)

            return await self.send_lend_tx(
                token_to_lend_with=token_to_withdraw,
                swap_data=swap_data,
                swap_info=swap_info,
                balance=balance,
                flag=False
            )

        except BaseException as e:
            logging.exception(f'Bend.lend/withdraw')
            return f'{failed_text}: {e}'
