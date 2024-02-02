import time
import random
from data.models import Settings
from typing import Optional

from sqlalchemy.orm import declarative_base
from libs.pretty_utils.type_functions.classes import AutoRepr
from sqlalchemy import (Column, Integer, Text, Boolean)
from data.models import WorkStatuses

# --- Wallets
Base = declarative_base()


class Wallet(Base, AutoRepr):
    __tablename__ = 'wallets'
    id = Column(Integer, primary_key=True)
    private_key = Column(Text, unique=True)
    address = Column(Text)
    name = Column(Text)
    proxy = Column(Text)
    next_pre_initial_action_time = Column(Integer)
    next_initial_action_time = Column(Integer)
    liquidity_added_timestamp = Column(Integer)
    swaps = Column(Integer)
    liquidity = Column(Integer)
    lending = Column(Integer)
    mint_nft = Column(Integer)
    dmail = Column(Integer)
    initial_completed = Column(Boolean)
    next_activity_action_time = Column(Integer)
    status = Column(Text)
    completed = Column(Boolean)

    def __init__(self, private_key: str, proxy: str, swaps: int, liquidity: int, lending: int,
                 dmail: int, mint_nft: int, address: Optional[str] = None, name: Optional[str] = None,
                 liquidity_added_timestamp: Optional[int] = None) -> None:
        now = int(time.time())
        settings = Settings()
        self.private_key = private_key
        self.address = address
        self.name = name
        self.proxy = proxy
        self.next_pre_initial_action_time = 0
        self.next_initial_action_time = 0
        self.liquidity_added_timestamp = 0
        self.swaps = swaps
        self.liquidity = liquidity
        self.lending = lending
        self.dmail = dmail
        self.mint_nft = mint_nft
        self.initial_completed = False
        self.next_activity_action_time = now + random.randint(0, int(settings.activity_actions_delay.to_ / 2))
        self.status = WorkStatuses.Activity
        self.completed = False
