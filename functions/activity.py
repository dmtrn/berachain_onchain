import time
import random
import asyncio
import logging
from typing import List

from libs.py_eth_async.client import Client
from libs.pretty_utils.miscellaneous.time_and_date import unix_to_strtime


from data import config
from data.models import Settings, Berachain, WorkStatuses
from utils.db_api.database import db
from utils.db_api.models import Wallet
from tasks.controller import Controller
from utils.encryption import get_private_key
from utils.miscellaneous.print_to_log import print_to_log
from utils.miscellaneous.print_summary import print_summary
from functions.select_random_action import select_random_action


async def update_expired() -> None:
    now = int(time.time())
    expired_wallets: List[Wallet] = db.all(
        Wallet, Wallet.status.is_(WorkStatuses.Activity) & (Wallet.next_activity_action_time <= now)
    )

    if expired_wallets:
        settings = Settings()
        for wallet in expired_wallets:
            wallet.next_activity_action_time = now + random.randint(0, int(settings.activity_actions_delay.to_ / 10))
            await print_to_log(
                text=f'Action time was re-generated: {unix_to_strtime(wallet.next_activity_action_time)}.',
                color=color, thread=thread, wallet=wallet
            )

        db.commit()


async def activity() -> None:
    delay = 10
    summary_print_time = 0
    next_message_time = 0
    await update_expired()
    await asyncio.sleep(5)
    while True:
        try:
            now = int(time.time())
            if summary_print_time <= now:
                await print_summary()
                summary_print_time = now + 30 * 60

            wallet: Wallet = db.one(
                Wallet, Wallet.next_activity_action_time <= now
            )
            if wallet:
                settings = Settings()
                client = Client(private_key=get_private_key(wallet.private_key), network=Berachain, proxy=wallet.proxy)
                controller = Controller(client=client)
                action = await select_random_action(controller=controller, wallet=wallet)
                now = int(time.time())

                if action == 'Insufficient balance':
                    wallet.next_activity_action_time = now + random.randint(
                        int(settings.activity_actions_delay.from_ / 10), int(settings.activity_actions_delay.to_ / 10)
                    )
                    await print_to_log(
                        text=f'Insufficient balance!', color=config.RED, thread=thread, wallet=wallet
                    )

                elif action:
                    status = await action()
                    now = int(time.time())
                    if 'Failed' not in status:
                        wallet.next_activity_action_time = now + random.randint(
                            settings.activity_actions_delay.from_, settings.activity_actions_delay.to_
                        )
                        print_color = color

                    else:
                        wallet.next_activity_action_time = now + random.randint(5 * 60, 10 * 60)
                        print_color = config.RED

                    await print_to_log(text=status, color=print_color, thread=thread, wallet=wallet)

                    try:
                        next_action_time = min((wallet.next_activity_action_time for wallet in db.all(
                            Wallet, Wallet.status.is_(WorkStatuses.Activity)
                        )))
                        await print_to_log(
                            text=f'The next closest action will be performed at {unix_to_strtime(next_action_time)}.',
                            color=color, thread=thread
                        )

                    except:
                        pass

                db.commit()

        except BaseException as e:
            logging.exception('activity')
            await print_to_log(text=f'Something went wrong: {e}', color=config.RED, thread=thread)

        finally:
            await asyncio.sleep(delay)


color = config.GREEN
thread = 'Activity'