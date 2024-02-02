import random
import time

from data.config import logger
from tasks.controller import Controller
from utils.db_api.models import Wallet
from functools import partial
from utils.db_api.database import db

from data.models import Settings, Ether


def action_add(
        available_action,
        token_name=None,
        swap=False,
        liquidity=False,
        lending=False,
        eth=False,
        nft=False,
):
    weight = 0.2
    if swap:
        token_list = [token_name] if not eth else available_action.AVAILABLE_SWAP
        action = available_action.swap_bera_to_token if eth else available_action.swap_to_bera
    elif liquidity:
        weight = 0.2
        token_list = [token_name]
        action = available_action.add_liquidity if eth else available_action.remove_liquidity
    elif lending:
        weight = 0.2
        token_list = [token_name]
        action = available_action.lend if eth else available_action.withdraw
    elif nft:
        weight = 0.2
        action = available_action.mint_honey_jar
        return [partial(action)], [weight]
    else:
        logger.error("GLOBAL ERROR IN ADDING ACTION")
    return [partial(action, token) for token in token_list], [weight for _ in token_list]


def check_eth_balance(eth_balance, settings, swap=True):
    if swap:
        return float(eth_balance.Ether) > float(settings.minimal_balance) * 2 + settings.eth_amount_for_swap.to_
    return float(eth_balance.Ether) > float(settings.minimal_balance)


async def add_swap_buying_action(wallet, possible_actions, weights, eth_balance, minimal_balance, settings, controller):
    sufficient_balance = check_eth_balance(eth_balance, settings)
    if sufficient_balance:
        for task in controller.swaps_tasks:
            actions, w = action_add(task, swap=True, eth=True)
            possible_actions.extend(actions)
            weights.extend(w)
    else:
        msg = (f'{wallet.address} | Insufficient balance. Swap ETH > any token action not possible. Reason: actual '
               f'ETH balance ({eth_balance.Ether}) must be more '
               f'({float(minimal_balance.Ether) * 2 + float(settings.eth_amount_for_swap.to_)}). Calculate: '
               f'minimal_balance * 2 + settigns.eth_amount_for_swap.to_')
        logger.warning(msg)


async def select_random_action(controller: Controller, wallet: Wallet, initial: bool = True):
    settings = Settings()
    possible_actions = []
    weights = []

    swaps = 0
    liquidity = 0
    lending = 0
    dmail = 0
    nft = 0

    eth_balance = await controller.client.wallet.balance()
    minimal_balance = Ether(settings.minimal_balance)

    if initial:
        # tx_total, swaps, lending, liquidity, nft, dmail = await controller.get_activity_count(wallet=wallet)
        # msg = (f'{wallet.address} | total tx/action tx: {tx_total}/{swaps + lending + nft + liquidity + dmail}'
        #        f' | amount swaps: {swaps}/{wallet.swaps}; amount add/remove lending: {lending}/{wallet.lending}'
        #        f' | amount LP: {liquidity}/{wallet.liquidity} amount NFT {nft}/{wallet.mint_nft}'
        #        f' | amount dmail {dmail}/{wallet.dmail}')
        msg = (f'{wallet.address} |')
        logger.info(msg)
        if (swaps >= wallet.swaps and lending >= wallet.lending
                and dmail >= wallet.dmail):
            return 'Processed'

    token_balances_dict, lending_token_balances_dict, liquidity_token_balances_dict = await controller.get_all_tokens()

    eth_balance = await controller.client.wallet.balance()
    sufficient_balance = check_eth_balance(eth_balance, settings, swap=False)

    # I - SWAPS
    if swaps < int(wallet.swaps) and sufficient_balance:
        # ETH -> Tokens
        await add_swap_buying_action(wallet,
                                     possible_actions,
                                     weights,
                                     eth_balance,
                                     minimal_balance,
                                     settings,
                                     controller
                                     )

        # Tokens -> ETH
        if token_balances_dict:
            for task in controller.swaps_tasks:
                available_tokens = [t for t in token_balances_dict.keys() if t.title in task.AVAILABLE_SWAP]
                for token in available_tokens:
                    actions, w = action_add(task, token.title, swap=True, eth=False)
                    possible_actions.extend(actions)
                    weights.extend(w)
    # II - LENDINGS
    if lending < int(wallet.lending):
        sufficient_balance = check_eth_balance(eth_balance, settings, swap=False)
        if token_balances_dict or sufficient_balance:
            # Add lending tasks
            for task in controller.lending_tasks:
                available_tokens = [(t, tk_balance) for t, tk_balance in token_balances_dict.items() if
                                    t.title in task.AVAILABLE_DEPOSIT]
                sufficient_balance = check_eth_balance(eth_balance, settings, swap=False)
                for token, tk_balance in available_tokens:
                    if sufficient_balance:
                        actions, w = action_add(task, token.title, lending=True, eth=True)
                        possible_actions.extend(actions)
                        weights.extend(w)

    # Remove lending #
    if lending_token_balances_dict:
        for task in controller.lending_tasks:
            available_lending_tokens = [t for t in lending_token_balances_dict.keys()
                                        if task.NAME in t.belongs_to]
            for token in available_lending_tokens:
                actions, w = action_add(task, token.token_out_name, lending=True, eth=False)  #
                possible_actions.extend(actions)
                weights.extend(w)

    # # III - LIQUIDITY
    if liquidity < int(wallet.liquidity): #
        if liquidity_token_balances_dict:
            if not wallet.liquidity_added_timestamp:
                msg = (f'{wallet.address} | This wallet already has liquidity token(s), but there is no information'
                       f' about liquidity_added_timestamp in database. We will add the current time as the '
                       f'liquidity added timestamp.')
                logger.warning(msg)
                wallet.liquidity_added_timestamp = int(time.time())
                db.commit()

        # add liquidity
        if wallet.liquidity_added_timestamp == 0:
            if token_balances_dict and not wallet.liquidity_added_timestamp:
                # Add liquidity tasks
                for task in controller.liquidity_tasks:
                    available_tokens = [(t, tk_balance) for t, tk_balance in token_balances_dict.items() if
                                        t.title in task.AVAILABLE_DEPOSIT]

                    for token, tk_balance in available_tokens:
                        # conditions = [
                        #     token.stable and eth_balance_diff > tk_balance.Ether,
                        #     not token.stable and eth_balance_diff >
                        #     TokenAmount(amount=float(tk_balance.Ether) * await Base.get_token_price(
                        #             token_symbol=token.name)).Ether
                        # ]
                        # if any(conditions):
                        actions, w = action_add(task, token.title, liquidity=True, eth=True)
                        possible_actions.extend(actions)
                        weights.extend(w)
    if liquidity_token_balances_dict:
        if (wallet.liquidity_added_timestamp and
                wallet.liquidity_added_timestamp + settings.liquidity_holding_time < int(time.time())):
            for task in controller.liquidity_tasks:
                available_liquidity_tokens = [t for t in liquidity_token_balances_dict.keys()
                                              if task.NAME in t.belongs_to]
                # available_liquidity_tokens = []
                # for t in liquidity_token_balances_dict.keys():
                #     if task.NAME in t.belongs_to:
                #         available_liquidity_tokens.append(t)
                for token in available_liquidity_tokens:
                    actions, w = action_add(task, token.title[1:], liquidity=True, eth=False)
                    possible_actions.extend(actions)
                    weights.extend(w)
    # # #

    if not liquidity_token_balances_dict and wallet.liquidity_added_timestamp != 0:
        wallet.liquidity_added_timestamp = 0
        db.commit()
    if nft < int(wallet.mint_nft):
        honey_balance = 0
        for token in token_balances_dict.keys():
            if token.title == "HONEY":
                honey_balance = token_balances_dict[token]
        if honey_balance > 4.2:
            actions, w = action_add(controller.honey_jar, nft=True)
            possible_actions.extend(actions)
            weights.extend(w)

    # print(f'Possible actions {len(possible_actions)} : {possible_actions}')
    if possible_actions:
        action = random.choices(possible_actions, weights=weights)[0]
        if action:
            return action

    msg = f'{controller.client.wallet} | select_random_action | can not choose the action'
    logger.info(msg)

    return None
