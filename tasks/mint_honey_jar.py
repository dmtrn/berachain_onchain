import random
import logging
import asyncio
from typing import Optional

from data.config import logger
from libs.py_eth_async.data.models import TokenAmount

from tasks.base import Base
from data.models import SwapInfo, Tokens, Routers, BaseContract


# Made by Alex Minterka < 4.2 Honey to mint
class HONEYJAR(Base):
    NAME = 'HONEY_JAR_MINT'
    AVAILABLE_DEPOSIT = ['HONEY']
    CONTRACT_MAP = {
        'HONEY': Tokens.HONEY,
    }

    async def prepare_data(self):
        swap_data = f'0xa6f2ae3a'
        return swap_data

    async def send_lend_tx(
            self,
            swap_data,
            swap_info: SwapInfo,
            token: Optional[BaseContract] = None,
            balance: Optional[TokenAmount] = None,
            test=False
    ):
        failed_text = f'Failed mint "Honey Jar" with {token.title} via {swap_info.swap_platform.title}'

        try:
            if test:
                print(swap_data)

            if token.title == 'HONEY':
                if not balance.Ether:
                    logger.error(f'{self.client.account.address} |'
                                 f'{swap_info.swap_platform.title} | mint | insufficient HONEY balance')
                    return f'{failed_text}: insufficient balance.'

            logger.info(f'{self.client.account.address} | {swap_info.swap_platform.title} | mint | '
                        f'{token.title} to "Honey Jar"')

            if not await self.approve_interface(
                    token_address=token.address,
                    spender=Routers.HONEY_JAR_MINT.address,
                    amount=TokenAmount(4200000000000000000, wei=True)
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
            if receipt:
                return (f'"Honey Jar" was minted with '
                        f'{swap_info.token_from.title}'
                        f' via {swap_info.swap_platform.title}: {tx.hash.hex()}')
            return f'Failed to swap via {swap_info.swap_platform.title}'

        except BaseException as e:
            logging.exception(f'{swap_info.swap_platform}.swap')
            return f'{failed_text}: {e}'

    async def mint_honey_jar(self) -> str:
        token = HONEYJAR.CONTRACT_MAP['HONEY']
        balance = await self.client.wallet.balance(
            token=token.address
        )

        swap_info = SwapInfo(
            token,
            token,
            Routers.HONEY_JAR_MINT
        )

        failed_text = f'Failed to mint "Honey Jar" with {token.title}  via {swap_info.swap_platform.title}'

        if balance.Ether >= 4.2:
            try:
                swap_data = await self.prepare_data()

                return await self.send_lend_tx(
                    token=token,
                    swap_data=swap_data,
                    swap_info=swap_info,
                    balance=balance
                )

            except BaseException as e:
                logging.exception(f'Honey.mint')
                return f'{failed_text}: {e}'
        else:
            logging.warning(f'Low Balance to Mint: balance of '
                            f'{token.title} = {balance.Ether}. Must be minimum 4.2 HONEY')
