import random
import logging
import asyncio
from typing import Optional

from data.config import logger
from libs.py_eth_async.data.models import TokenAmount

from tasks.base import Base
from data.models import SwapInfo, Tokens, Routers, BaseContract


# Made by Alex Swapalka
class HONEY(Base):
    NAME = 'HONEY_MINT'
    AVAILABLE_SWAP = ['STGUSDC', 'HONEY']
    CONTRACT_MAP = {
        'HONEY': Tokens.HONEY,
        'STGUSDC': Tokens.STGUSDC,
    }

    async def prepare_data(self, from_token, balance: Optional[TokenAmount]):
        swap_data = (f'0xc6c3bbe6'
                     f'{self.client.account.address[2:].zfill(64)}'
                     f'{from_token.address[2:].zfill(64)}'
                     f'{hex(int(balance.Wei * 0.3))[2:].zfill(64)}'
                     )
        return swap_data

    async def send_lend_tx(
            self,
            from_token,
            swap_data,
            swap_info: SwapInfo,
            to_token: Optional[BaseContract] = None,
            balance: Optional[TokenAmount] = None,
            test=False
    ):
        failed_text = f'Failed swap {from_token.title} to {to_token.title} via {swap_info.swap_platform.title}'

        try:
            if test:
                print(swap_data)

            if from_token.title == 'STGUSDC':
                if not balance.Ether:
                    logger.error(f'{self.client.account.address} |'
                                 f'{swap_info.swap_platform.title} | swap | insufficient STGUSDC balance')
                    return f'{failed_text}: insufficient balance.'

            logger.info(f'{self.client.account.address} | {swap_info.swap_platform.title} | mint | '
                        f'{from_token.title} to {to_token.title} amount: {(int(balance.Wei * 0.3)) / 10 ** 18}')

            if not await self.approve_interface(
                    token_address=from_token.address,
                    spender=Routers.HONEY_MINT.address,
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
            if receipt:
                return (f'{(int(balance.Wei * 0.3)) / 10 ** 18} {to_token.title} was minted to'
                        f' {swap_info.token_from.title}'
                        f' via {swap_info.swap_platform.title}: {tx.hash.hex()}')
            return f'Failed to swap via {swap_info.swap_platform.title}'

        except BaseException as e:
            logging.exception(f'{swap_info.swap_platform}.swap')
            return f'{failed_text}: {e}'

    async def mint_honey(self) -> str:
        from_token = HONEY.CONTRACT_MAP['STGUSDC']
        to_token = HONEY.CONTRACT_MAP['HONEY']
        balance = await self.client.wallet.balance(
            token=from_token.address
        )

        if not balance:
            return "No balance"


        swap_info = SwapInfo(
            from_token,
            to_token,
            Routers.HONEY_MINT
        )

        failed_text = f'Failed to mint {from_token.title}  via {swap_info.swap_platform.title}'

        try:
            swap_data = await self.prepare_data(from_token, balance)

            return await self.send_lend_tx(
                from_token=from_token,
                to_token=to_token,
                swap_data=swap_data,
                swap_info=swap_info,
                balance=balance
            )

        except BaseException as e:
            logging.exception(f'Honey.mint')
            return f'{failed_text}: {e}'
