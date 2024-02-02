from libs.py_eth_async.client import Client

from utils.db_api.models import Wallet
from tasks.base import Base

from tasks.bex import BEX
from tasks.honey import HONEY
from tasks.algebra_finance import Algebra
from tasks.mint_honey_jar import HONEYJAR
from tasks.bend import BEND
from tasks.bex_lp import BexLP


class Controller(Base):
    def __init__(self, client: Client):
        super().__init__(client)
        self.base = Base(client=client)
        self.bex = BEX(client=client)
        self.algebra = Algebra(client=client)
        self.honey = HONEY(client=client)
        self.honey_jar = HONEYJAR(client=client)
        self.bend = BEND(client=client)
        self.bex_lp = BexLP(client=client)

        self.swaps_tasks = [self.bex, self.algebra]  # TODO add all possible swap tasks
        self.lending_tasks = [self.bend]  # TODO add all possible Lendings
        self.liquidity_tasks = [self.bex_lp]  # TODO add all possible Liquidity

    async def get_activity_count(self, wallet: Wallet = None):
        tx_total, swaps, lending, liquidity, nft, dmail = 0, 0, 0, 0, 0, 0
        return tx_total, swaps, lending, liquidity, nft, dmail
