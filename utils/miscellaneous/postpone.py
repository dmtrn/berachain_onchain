import time
import random
from typing import Optional, List

from data.models import Settings, WorkStatuses
from utils.db_api.database import db
from utils.db_api.models import Wallet


async def postpone(seconds: Optional[int] = 0, status: str = WorkStatuses.Initial):
    settings = Settings()
    wallets: List[Wallet] = db.all(Wallet, Wallet.status.is_(status))

    for wallet in wallets:
        now = int(time.time())
        if status == WorkStatuses.Activity:
            if wallet.next_activity_action_time <= now:
                wallet.next_activity_action_time = now + random.randint(
                    0, int(settings.activity_actions_delay.to_ / 10)
                )

            elif seconds:
                wallet.next_activity_action_time = wallet.next_activity_action_time + seconds

        else:
            if wallet.next_initial_action_time <= now:
                wallet.next_initial_action_time = now + random.randint(0, int(settings.initial_actions_delay.to_ / 2))

            elif seconds:
                wallet.next_initial_action_time = wallet.next_initial_action_time + seconds

        db.commit()
