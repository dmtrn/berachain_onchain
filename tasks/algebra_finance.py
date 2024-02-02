import random
import asyncio
import json
import aiohttp
import time

from fake_useragent import UserAgent
from loguru import logger
from libs.py_eth_async.data.models import TokenAmount

from tasks.base import Base
from data.models import Tokens, Routers, BaseContract


# Mady by Toby Swapalka
class Algebra(Base):
    NAME = 'Algebra'
    AVAILABLE_SWAP = ['STGUSDC']
    CONTRACT_MAP = {
        'WBERA': Tokens.WBERA,
        'STGUSDC': Tokens.STGUSDC,
    }

    # async def swap(self, to_token: str):
    #     if to_token in self.AVAILABLE_SWAP:
    #         try:
    #             if to_token == 'BERA':
    #                 to_token = self.CONTRACT_MAP['WBERA']
    #                 token_out = self.CONTRACT_MAP['STGUSDC']
    #                 amount, swap_data, failed_text = await self.swap_data_bera(to_token=to_token, token_out=token_out)
    #             else:
    #                 to_token = self.CONTRACT_MAP['STGUSDC']
    #                 token_out = self.CONTRACT_MAP['WBERA']
    #                 amount, swap_data, failed_text = await self.swap_data_stgusdc(to_token=to_token, token_out=token_out)
    #             await self.tx_build(token=to_token, amount=amount, swap_data=swap_data, failed_text=failed_text)
    #
    #         except BaseException as e:
    #             logger.exception(f'{self.NAME}.wrap')
    #             return f'Fail swap via {self.NAME}: {e}'
    #     else:
    #         logger.error(f'{self.client.account.address} via'
    #                      f"{self.NAME} can't find token: '{to_token}' ")
    #         return

    async def swap_bera_to_token(self, token: str):
        if token == 'BERA':
            try:
                to_token = self.CONTRACT_MAP['WBERA']
                token_out = self.CONTRACT_MAP['STGUSDC']
                amount, swap_data, failed_text = await self.swap_data_bera(to_token=to_token, token_out=token_out)
                await self.tx_build(token=to_token, amount=amount, swap_data=swap_data, failed_text=failed_text)
            except BaseException as e:
                logger.exception(f'{self.NAME}.wrap')
                return f'Fail swap via {self.NAME}: {e}'
        else:
            logger.error(f'{self.client.account.address} via'
                         f"{self.NAME} can't find token: '{token}' ")

    async def swap_to_bera(self, token: str):
        if token == 'STGUSDC':
            try:
                to_token = self.CONTRACT_MAP['STGUSDC']
                token_out = self.CONTRACT_MAP['WBERA']
                amount, swap_data, failed_text = await self.swap_data_stgusdc(to_token=to_token, token_out=token_out)
                await self.tx_build(token=to_token, amount=amount, swap_data=swap_data, failed_text=failed_text)
            except BaseException as e:
                logger.exception(f'{self.NAME}.wrap')
                return f'Fail swap via {self.NAME}: {e}'
        else:
            logger.error(f'{self.client.account.address} via'
                         f"{self.NAME} can't find token: '{token}' ")


    async def swap_data_bera(self, to_token: BaseContract, token_out: BaseContract):
        failed_text = f'Failed to swap {to_token.title} in {token_out.title} via {self.NAME}'
        ask_stgusdc = 1
        slippage = 1

        amount = self.get_random_amount()
        bear_price, fee = await self._bera_price(which_token=ask_stgusdc)
        amount_out = TokenAmount(amount=float(amount.Ether) * bear_price)
        amount_out_with_fee = TokenAmount(
            amount=(float(amount_out.Ether) * (1 - slippage / 100)) * (1 - (int(fee)/10000) / 100)
        )
        swap_data = (f'0xac9650d8'
                     f'0000000000000000000000000000000000000000000000000000000000000020'
                     f'0000000000000000000000000000000000000000000000000000000000000001'
                     f'0000000000000000000000000000000000000000000000000000000000000020'
                     f'00000000000000000000000000000000000000000000000000000000000000e4bc651188'  # Const HUI_ZNAET WHAT IS IT
                     f'{to_token.address.lower()[2:]:0>64}'
                     f'{token_out.address.lower()[2:]:0>64}'
                     f'{self.client.account.address.lower()[2:]:0>64}'
                     f'{hex(int((time.time() + 60 * 20) * 1000) + random.randint(1,999))[2:]:0>64}'
                     f'{hex(amount.Wei)[2:]:0>64}'
                     f'{hex(amount_out_with_fee.Wei)[2:]:0>64}'
                     f'0000000000000000000000000000000000000000000000000000000000000000'
                     f'00000000000000000000000000000000000000000000000000000000'
                     )
        return amount, swap_data, failed_text

    async def swap_data_stgusdc(self, to_token: BaseContract, token_out: BaseContract):
        failed_text = f'Failed to swap {to_token.title} in {token_out.title} via {self.NAME}'
        ask_stgusdc = 0
        slippage = 1
        amount = await self.client.wallet.balance(token=to_token)

        bear_price, fee = await self._bera_price(which_token=ask_stgusdc)
        amount_out = TokenAmount(amount=float(amount.Ether) * bear_price)
        amount_out_with_fee = TokenAmount(
            amount=(float(amount_out.Ether) * (1 - slippage / 100)) * (1 - (int(fee)/10000) / 100)
        )
        swap_data = (f'0xac9650d8'
                     f'0000000000000000000000000000000000000000000000000000000000000020'
                     f'0000000000000000000000000000000000000000000000000000000000000002'
                     f'0000000000000000000000000000000000000000000000000000000000000040'
                     f'0000000000000000000000000000000000000000000000000000000000000160'
                     f'00000000000000000000000000000000000000000000000000000000000000e4bc651188'  # Const HUI_ZNAET WHAT IS IT
                     f'{to_token.address.lower()[2:]:0>64}'  # To-token address 
                     f'{token_out.address.lower()[2:]:0>64}'  # Token_out address 
                     f'0000000000000000000000000000000000000000000000000000000000000000'
                     f'{hex(int((time.time() + 60 * 20) * 1000) + random.randint(1,999))[2:]:0>64}'
                     f'{hex(amount.Wei)[2:]:0>64}'  # To-token amount
                     f'{hex(amount_out_with_fee.Wei)[2:]:0>64}'  # Token-out amount 
                     f'0000000000000000000000000000000000000000000000000000000000000000'
                     f'0000000000000000000000000000000000000000000000000000000000000000'
                     f'0000000000000000000000000000000000000000000000000000004469bc35b2'  # Const HUI_ZNAET WHAT IS IT
                     f'{hex(amount_out_with_fee.Wei)[2:]:0>64}'  # Token-out amount 
                     f'{self.client.account.address.lower()[2:]:0>64}'
                     f'00000000000000000000000000000000000000000000000000000000')
        return amount, swap_data, failed_text

    async def tx_build(self, token: BaseContract, swap_data,
                       failed_text, test=False, amount: TokenAmount = 0):
        try:
            if test:
                print(swap_data)

            if token.title == 'STGUSDC':
                if not await self.approve_interface(
                        token_address=token.address,
                        spender=Routers.ALGEBRA.address,
                        amount=amount
                ):
                    return f'{failed_text}: token not approved.'
                await asyncio.sleep(random.randint(15, 25))

            logger.info(f'{self.client.account.address} | '
                        f'{failed_text[10:]} | amount: {amount.Ether}')

            tx_params = {
                'chainId': self.client.network.chain_id,
                'nonce': await self.client.wallet.nonce(),
                'from': self.client.account.address,
                'to': Routers.ALGEBRA.address,
                'data': swap_data,
                'value': 0 if token.title != 'WBERA' else amount.Wei,
            }

            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)
            # receipt, tx_hash = await self.submit_transaction(tx_params)
            if isinstance(receipt, dict):
                logger.success(f'{amount.Ether} {failed_text[10:]}: {tx.hash.hex()}')
                return (f'{amount.Ether} '
                        f'{failed_text[10:]}: {tx.hash.hex()}')
            return f'{failed_text} | In build_tx'

        except BaseException as e:
            logger.exception(f'{self.NAME}.swap')
            return f'{failed_text}: {e}'

    async def _bera_price(self, which_token: int, max_retries: int = 5,):
        user_agent = UserAgent().chrome
        version = user_agent.split('Chrome/')[1].split('.')[0]
        platform = ['macOS', 'Windows', 'Linux']
        headers = {
            'authority': f'api.goldsky.com',
            'accept': f'*/*',
            'accept-language': f'en-US,en;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': f'application/json',
            'dnt': f'1',
            'origin': f'https://berachain.algebra.finance',
            'referer': f'https://berachain.algebra.finance/',
            'sec-ch-ua': f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not_A Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{platform}"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'sec-gpc': '1',
            'user-agent': user_agent,
        }

        json_data = {
            'operationName': 'SinglePool',
            'variables': {
                'poolId': '0x0e6ab429c8fb5e0ed293d762f4babc32298c56b8',
            },
            'query': 'query SinglePool($poolId: ID!) {\n  pool(id: $poolId) {\n    ...PoolFields\n    __typename\n  }\n}\n\nfragment PoolFields on Pool {\n  id\n  fee\n  token0 {\n    ...TokenFields\n    __typename\n  }\n  token1 {\n    ...TokenFields\n    __typename\n  }\n  sqrtPrice\n  liquidity\n  tick\n  tickSpacing\n  totalValueLockedUSD\n  volumeUSD\n  feesUSD\n  untrackedFeesUSD\n  token0Price\n  token1Price\n  __typename\n}\n\nfragment TokenFields on Token {\n  id\n  symbol\n  name\n  decimals\n  derivedMatic\n  __typename\n}',
        }

        data_str = json.dumps(json_data)

        for _ in range(max_retries):
            try:
                connector = self.get_session()
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with await session.post(
                            url='https://api.goldsky.com/api/public/project_clroqsly50az501z69zgz01qa/subgraphs/bera-analytics/1.0.1/gn',
                            headers=headers,
                            data=data_str
                    ) as r:
                        result = (await r.json())
                        if result is not False:
                            return float(result['data']['pool'][f'token{which_token}Price']), result['data']['pool']['fee']
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(1)
        return 'Error with take price for BERA | ALGEBRA API problem!'

