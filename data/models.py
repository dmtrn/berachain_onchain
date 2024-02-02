import inspect

from dataclasses import dataclass
from typing import Union, Optional
from decimal import Decimal
from eth_utils import to_wei, from_wei

from libs.py_okx_async.models import OKXCredentials
from libs.pretty_utils.miscellaneous.files import read_json
from libs.py_eth_async.data.models import Network, GWei, RawContract
from libs.pretty_utils.type_functions.classes import AutoRepr, Singleton, ArbitraryAttributes

from data.config import ABIS_DIR
from libs.py_eth_async.data.models import DefaultABIs

from data.config import SETTINGS_FILE


class ProgramActions:
    ImportWallets = ArbitraryAttributes(Selection=1)
    StartScript = ArbitraryAttributes(Selection=2)

@dataclass
class FromTo:
    from_: Union[int, float]
    to_: Union[int, float]


class BaseContract(RawContract):
    def __init__(self,
                 title,
                 address,
                 abi,
                 min_value: Optional[float] = 0,
                 stable: Optional[bool] = False,
                 belongs_to: Optional[str] = "",
                 decimals: Optional[int] = 18,
                 token_out_name: Optional[str] = '',
                 ):
        super().__init__(address, abi)
        self.title = title
        self.min_value = min_value
        self.stable = stable
        self.belongs_to = belongs_to  # Имя помойки например AAVE
        self.decimals = decimals
        self.token_out_name = token_out_name


class SwapInfo:
    def __init__(self, token_from: BaseContract, token_to: BaseContract, swap_platform: BaseContract):
        self.token_from = token_from
        self.token_to = token_to
        self.swap_platform = swap_platform


class OkxModel:
    required_minimum_balance: float
    withdraw_amount: FromTo
    delay_between_withdrawals: FromTo
    credentials: OKXCredentials


class WorkStatuses:
    BEX_complete = 'bex_completed'
    honey_minted = 'honey_minted'
    NotStarted = 'not_started'
    No_balance = 'no_balance'
    # Bridged = 'bridged'
    # Filled = 'filled'
    Initial = 'initial'
    Activity = 'activity'


@dataclass
class BinanceCredentials:
    """
    An instance that contains OKX API key data.

    Attributes:
        api_key (str): an API key.
        secret_key (str): a secret key.
        passphrase (str): a passphrase.

    """
    api_key: str
    secret_key: str

    def completely_filled(self) -> bool:
        """
        Check if all required attributes are specified.

        Returns:
            bool: True if all required attributes are specified.

        """
        return all((self.api_key, self.secret_key))


class BinanceModel:
    required_minimum_balance: float
    withdraw_amount: FromTo
    delay_between_withdrawals: FromTo
    credentials: BinanceCredentials


class Settings(Singleton, AutoRepr):
    def __init__(self):
        json = read_json(path=SETTINGS_FILE)

        self.use_private_key_encryption = json['use_private_key_encryption']
        # self.networks = UsedNetworks()

        # self.rpcs = json['networks']['EVM_chain']['rpcs']
        self.rpcs = json['networks']['Scroll']['rpcs']
        self.okx_withdrawls_timestamp: int = json['okx_withdrawls_timestamp']

        self.okx = OkxModel()
        self.okx.withdraw_amount = FromTo(
            from_=json['okx']['withdraw_amount']['from'],
            to_=json['okx']['withdraw_amount']['to'],
        )
        self.okx.delay_between_withdrawals = FromTo(
            from_=json['okx']['delay_between_withdrawals']['from'],
            to_=json['okx']['delay_between_withdrawals']['to'],
        )
        self.okx.required_minimum_balance = json['okx']['required_minimum_balance']
        self.okx.credentials = OKXCredentials(
            api_key=json['okx']['credentials']['api_key'],
            secret_key=json['okx']['credentials']['secret_key'],
            passphrase=json['okx']['credentials']['passphrase']
        )

        self.binance = BinanceModel()
        self.binance.withdraw_amount = FromTo(
            from_=json['binance']['withdraw_amount']['from'],
            to_=json['binance']['withdraw_amount']['to'],
        )
        self.binance.delay_between_withdrawals = FromTo(
            from_=json['binance']['delay_between_withdrawals']['from'],
            to_=json['binance']['delay_between_withdrawals']['to'],
        )
        self.binance.required_minimum_balance = json['binance']['required_minimum_balance']
        self.binance.credentials = BinanceCredentials(
            api_key=json['binance']['credentials']['api_key'],
            secret_key=json['binance']['credentials']['secret_key'],
        )

        self.oklink_api_key = json['oklink_api_key']
        self.usd_threshold = json['usd_threshold']

        self.minimal_balance: float = json['minimal_balance']
        self.txs_after_timestamp: int = json['txs_after_timestamp']
        self.use_official_bridge: bool = json['use_official_bridge']
        self.maximum_gas_price: GWei = GWei(json['maximum_gas_price'])
        self.initial_actions_delay: FromTo = FromTo(
            from_=json['initial_actions_delay']['from'], to_=json['initial_actions_delay']['to']
        )

        self.swaps: FromTo = FromTo(from_=json['swaps']['from'], to_=json['swaps']['to'])
        self.dmail: FromTo = FromTo(from_=json['dmail']['from'], to_=json['dmail']['to'])
        self.lending: FromTo = FromTo(from_=json['liquidity']['from'], to_=json['liquidity']['to'])
        self.liquidity: FromTo = FromTo(from_=json['liquidity']['from'], to_=json['liquidity']['to'])
        self.liquidity_holding_time = json['liquidity_holding_time']

        self.eth_amount_for_swap: FromTo = FromTo(
            from_=json['eth_amount_for_swap']['from'], to_=json['eth_amount_for_swap']['to']
        )
        self.eth_amount_for_bridge: FromTo = FromTo(
            from_=json['eth_amount_for_bridge']['from'], to_=json['eth_amount_for_bridge']['to']
        )
        self.activity_actions_delay: FromTo = FromTo(
            from_=json['activity_actions_delay']['from'], to_=json['activity_actions_delay']['to']
        )
        self.eth_amount_for_liquidity: FromTo = FromTo(
            from_=json['eth_amount_for_liquidity']['from'], to_=json['eth_amount_for_liquidity']['to']
        )

        self.amount_to_bridge: FromTo = FromTo(from_=json['amount_to_bridge']['from'],
                                               to_=json['amount_to_bridge']['to'])
        self.pre_initial_actions_delay: FromTo = FromTo(
            from_=json['pre_initial_actions_delay']['from'], to_=json['pre_initial_actions_delay']['to']
        )
        self.mint_nft: FromTo = FromTo(from_=json['mint_nft']['from'],
                                       to_=json['mint_nft']['to'])
        self.dest_chain_fee: FromTo = FromTo(
            from_=json['dest_chain_fee']['from'], to_=json['dest_chain_fee']['to']
        )
        self.available_networks = json['available_networks']


settings = Settings()

BaseNetwork = Network(
    name='Base',
    rpc='https://base.llamarpc.com',
    chain_id=8453,
    tx_type=2,
    coin_symbol='ETH',
    explorer='https://explorer.zora.energy',
)

Berachain = Network(
    name='Berachain Artio',
    # rpc="https://rpc.ankr.com/berachain_testnet",
    # rpc="https://berachain-artio.rpc.thirdweb.com",
    rpc="https://artio.rpc.berachain.com/",
    chain_id=80085,
    tx_type=2,
    coin_symbol='BERA',
    explorer='https://artio.beratrail.io/',
)

Linea = Network(
    name='Linea',
    rpc='https://1rpc.io/linea',
    chain_id=59144,
    tx_type=2,
    coin_symbol='ETH',
    explorer='https://lineascan.build',
)

Arbitrum = Network(
    name='Arbitrum One',
    rpc='https://rpc.ankr.com/arbitrum/',
    chain_id=42161,
    tx_type=2,
    coin_symbol='ETH',
    explorer='https://arbiscan.io/',
)

Optimism = Network(
    name='Optimism',
    rpc='https://rpc.ankr.com/optimism/',
    chain_id=10,
    tx_type=2,
    coin_symbol='ETH',
    explorer='https://optimistic.etherscan.io/',
)

BERACHAIN = Network(
    name='Base',
    rpc='https://artio.rpc.berachain.com',
    chain_id=80085,
    tx_type=0,
    coin_symbol='ETH',
    explorer='https://basescan.org',
)


class Routers(Singleton):
    """
    An instance with router contracts
        variables:
            ROUTER: BaseContract
            ROUTER.title = any
    """
    BEX_WETH = BaseContract(
        title="BEX_WETH", address='0x5806E416dA447b267cEA759358cF22Cc41FAE80F',
        abi=read_json(path=(ABIS_DIR, 'blank.json'))
    )
    BEX = BaseContract(
        title="BEX", address='0x0d5862FDbdd12490f9b4De54c236cff63B038074',
        abi=read_json(path=(ABIS_DIR, 'blank.json'))
    )
    HONEY_MINT = BaseContract(
        title="HONEY_MINT", address='0x09ec711b81cD27A6466EC40960F2f8D85BB129D9',
        abi=read_json(path=(ABIS_DIR, 'honey_mint.json'))
    )
    HONEY_JAR_MINT = BaseContract(
        title="HONEY_JAR_MINT", address='0x6553444CaA1d4FA329aa9872008ca70AE6131925',
        abi=read_json(path=(ABIS_DIR, 'honey_jar.json'))
    )
    BEND = BaseContract(
        title="BEND", address='0xA691f7CfB3C65A17Dcbf9D6d748Cc677B0640db0',
        abi=read_json(path=(ABIS_DIR, 'bend.json'))
    )
    ALGEBRA = BaseContract(
        title='ALGEBRA', address='0x24592c979f1A9F664c22652764879548080Afb34',
        abi=DefaultABIs.Token
    )
    DEPOSIT_POOL_BEX = BaseContract(
        title='BEX_LP', address='0x0d5862FDbdd12490f9b4De54c236cff63B038074',
        abi=DefaultABIs.Token
    )


class Tokens(Singleton):
    """
    An instance with token contracts
        variables:
            TOKEN: BaseContract
            TOKEN.title = symbol from OKLINK
    """
    WBERA = BaseContract(
        title="WBERA", address='0x5806E416dA447b267cEA759358cF22Cc41FAE80F',

        abi=DefaultABIs.Token,
        decimals=18
    )
    BERA = BaseContract(
        title="BERA", address='0x0000000000000000000000000000000000000000',
        abi=DefaultABIs.Token,
        decimals=18
    )
    STGUSDC = BaseContract(
        title="STGUSDC", address='0x6581e59A1C8dA66eD0D313a0d4029DcE2F746Cc5',
        abi=DefaultABIs.Token,
        decimals=18
    )
    HONEY = BaseContract(
        title="HONEY", address='0x7EeCA4205fF31f947EdBd49195a7A88E6A91161B',
        abi=DefaultABIs.Token,
        decimals=18
    )
    WBTC = BaseContract(
        title="WBTC", address='0x9DAD8A1F64692adeB74ACa26129e0F16897fF4BB',
        abi=DefaultABIs.Token,
        decimals=8
    )
    WETH = BaseContract(
        title="WETH", address='0x8239FBb3e3D0C2cDFd7888D8aF7701240Ac4DcA4',
        abi=DefaultABIs.Token,
        decimals=18,
    )

    @staticmethod
    def get_token_list():
        return [
            value for name, value in inspect.getmembers(Tokens)
            if isinstance(value, BaseContract)
        ]


class Pools(Singleton):
    """
        An instance with pool contracts
            variables:
                POOL: BaseContract
                POOL.TITLE = any
    """
    BERA_STGUSDC = BaseContract(
        title="BERA_STGUSDC", address='0x36af4fbab8ebe58b4effe0d5d72ceffc6efc650a',
        abi=DefaultABIs.Token
    )
    STGUSDC_HONEY = BaseContract(
        title="STGUSDC_HONEY", address='0xaebf2a333755d2783ab2a8e8bf30b49e254926cb',
        abi=DefaultABIs.Token
    )
    WERA_WBTC = BaseContract(
        title="WERA_WBTC", address='0xd3c962f3f36484439a41d0e970cf6581ddf0a9a1',
        abi=DefaultABIs.Token
    )
    WBERA_WETH = BaseContract(
        title="WBERA_WETH", address='0xd3c962f3f36484439a41d0e970cf6581ddf0a9a1',
        abi=DefaultABIs.Token
    )
    WBTC_HONEY_POOL = BaseContract(
        title='WBTC_HONEY', address='0x751524e7badd31d018a4caf4e4924a21b0c13cd0',
        abi=DefaultABIs.Token
    )
    WETH_HONEY_POOL = BaseContract(
        title='WETH_HONEY', address='0x101f52c804c1c02c0a1d33442eca30ecb6fb2434',
        abi=DefaultABIs.Token
    )
    STGUSDC_HONEY_POOL = BaseContract(
        title='STGUSDC_HONEY', address='0x5479fbdef04302d2deef0cc78f7d503d81fdfcc9',
        abi=DefaultABIs.Token
    )


class Lending_Tokens(Singleton):
    """
        An instance with lending contracts
            variables:
                LENDING_TOKEN: BaseContract
                LENDING_TOKEN.title = symbol from Oklink
    """
    aHONEY = BaseContract(
        title='aHONEY', address='0xB74285805B9eb4Dad384431C51F64C71fB786523',
        abi=DefaultABIs.Token,
        belongs_to="BEND",
        token_out_name='HONEY'

    )
    aWETH = BaseContract(
        title='aWETH', address='0xE76867589D0C6C43eeFb9e0d9AcAFC7deD8a2861',
        abi=DefaultABIs.Token,
        belongs_to="BEND",
        token_out_name='WETH'

    )
    aWBTC = BaseContract(
        title='aWBTC', address='0x1fa71FAa2E39Bd1A14628D25C25c2E6e0F66340A',
        abi=DefaultABIs.Token,
        belongs_to="BEND",
        token_out_name='WBTC'
    )

    @staticmethod
    def get_token_list():
        return [
            value for name, value in inspect.getmembers(Lending_Tokens)
            if isinstance(value, BaseContract)
        ]


class Liquidity_Tokens(Singleton):
    """
        An instance with LP contracts
            variables:
                LP_TOKEN: BaseContract
                LP_TOKEN.title = symbol from Oklink
     """
    WBTC_HONEY_POOL_SPECIAL = BaseContract(
        title='WBTC_HONEY', address='0xa85579e75a7ba99d00cce02441a5e21661b63a98',
        abi=DefaultABIs.Token,
        belongs_to='BexLP'
    )
    WETH_HONEY_POOL_SPECIAL = BaseContract(
        title='WETH_HONEY', address='0x599d8d33253361f1dc654e6f9c2813bd392ec0d5',
        abi=DefaultABIs.Token,
        belongs_to='BexLP'
    )
    STGUSDC_HONEY_POOL_SPECIAL = BaseContract(
        title='STGUSDC_HONEY', address='0xc70c2fd8f8e3dbbb6f73502c70952f115bb93929',
        abi=DefaultABIs.Token,
        belongs_to='BexLP'
    )

    @staticmethod
    def get_token_list():
        return [
            value for name, value in inspect.getmembers(Liquidity_Tokens)
            if isinstance(value, BaseContract)
        ]


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        """
        A token amount instance.

        :param Union[int, float, str, Decimal] amount: an amount
        :param int decimals: the decimals of the token (18)
        :param bool wei: the 'amount' is specified in Wei (False)
        """
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


unit_denominations = {
    'wei': 10 ** -18,
    'kwei': 10 ** -15,
    'mwei': 10 ** -12,
    'gwei': 10 ** -9,
    'szabo': 10 ** -6,
    'finney': 10 ** -3,
    'ether': 1,
    'kether': 10 ** 3,
    'mether': 10 ** 6,
    'gether': 10 ** 9,
    'tether': 10 ** 12,
}


class Unit(AutoRepr):
    """
    An instance of an Ethereum unit.

    Attributes:
        unit (str): a unit name.
        decimals (int): a number of decimals.
        Wei (int): the amount in Wei.
        KWei (Decimal): the amount in KWei.
        MWei (Decimal): the amount in MWei.
        GWei (Decimal): the amount in GWei.
        Szabo (Decimal): the amount in Szabo.
        Finney (Decimal): the amount in Finney.
        Ether (Decimal): the amount in Ether.
        KEther (Decimal): the amount in KEther.
        MEther (Decimal): the amount in MEther.
        GEther (Decimal): the amount in GEther.
        TEther (Decimal): the amount in TEther.

    """
    unit: str
    decimals: int
    Wei: int
    KWei: Decimal
    MWei: Decimal
    GWei: Decimal
    Szabo: Decimal
    Finney: Decimal
    Ether: Decimal
    KEther: Decimal
    MEther: Decimal
    GEther: Decimal
    TEther: Decimal

    def __init__(self, amount: Union[int, float, str, Decimal], unit: str) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.
            unit (str): a unit name.

        """
        self.unit = unit
        self.decimals = 18
        self.Wei = to_wei(amount, self.unit)
        self.KWei = from_wei(self.Wei, 'kwei')
        self.MWei = from_wei(self.Wei, 'mwei')
        self.GWei = from_wei(self.Wei, 'gwei')
        self.Szabo = from_wei(self.Wei, 'szabo')
        self.Finney = from_wei(self.Wei, 'finney')
        self.Ether = from_wei(self.Wei, 'ether')
        self.KEther = from_wei(self.Wei, 'kether')
        self.MEther = from_wei(self.Wei, 'mether')
        self.GEther = from_wei(self.Wei, 'gether')
        self.TEther = from_wei(self.Wei, 'tether')

    def __add__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(self.Wei + other.Wei)

        elif isinstance(other, int):
            return Wei(self.Wei + other)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei + GWei(other).GWei)

            else:
                return Ether(self.Ether + Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __radd__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(other.Wei + self.Wei)

        elif isinstance(other, int):
            return Wei(other + self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei + self.GWei)

            else:
                return Ether(Ether(other).Ether + self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __sub__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(self.Wei - other.Wei)

        elif isinstance(other, int):
            return Wei(self.Wei - other)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei - GWei(other).GWei)

            else:
                return Ether(self.Ether - Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __rsub__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(other.Wei - self.Wei)

        elif isinstance(other, int):
            return Wei(other - self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei - self.GWei)

            else:
                return Ether(Ether(other).Ether - self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __mul__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(self.Ether)) * Decimal(str(other.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(self.Wei * other.Wei / denominations)

        elif isinstance(other, int):
            return Wei(self.Wei * other)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei * GWei(other).GWei)

            else:
                return Ether(self.Ether * Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __rmul__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(other.Ether)) * Decimal(str(self.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(other.Wei * self.Wei / denominations)

        elif isinstance(other, int):
            return Wei(other * self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei * self.GWei)

            else:
                return Ether(Ether(other).Ether * self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __truediv__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(self.Ether)) / Decimal(str(other.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(self.Wei / other.Wei * denominations)

        elif isinstance(other, int):
            return Wei(self.Wei / Decimal(str(other)))

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei / GWei(other).GWei)

            else:
                return Ether(self.Ether / Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __rtruediv__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(other.Ether)) / Decimal(str(self.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(other.Wei / self.Wei * denominations)

        elif isinstance(other, int):
            return Wei(Decimal(str(other)) / self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei / self.GWei)

            else:
                return Ether(Ether(other).Ether / self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __iadd__(self, other):
        return self.__add__(other)

    def __isub__(self, other):
        return self.__sub__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __lt__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei < other.Wei

        elif isinstance(other, int):
            return self.Wei < other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei < GWei(other).GWei

            else:
                return self.Ether < Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __le__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei <= other.Wei

        elif isinstance(other, int):
            return self.Wei <= other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei <= GWei(other).GWei

            else:
                return self.Ether <= Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __eq__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei == other.Wei

        elif isinstance(other, int):
            return self.Wei == other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei == GWei(other).GWei

            else:
                return self.Ether == Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __ne__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei != other.Wei

        elif isinstance(other, int):
            return self.Wei != other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei != GWei(other).GWei

            else:
                return self.Ether != Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __gt__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei > other.Wei

        elif isinstance(other, int):
            return self.Wei > other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei > GWei(other).GWei

            else:
                return self.Ether > Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __ge__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei >= other.Wei

        elif isinstance(other, int):
            return self.Wei >= other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei >= GWei(other).GWei

            else:
                return self.Ether >= Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")


class Wei(Unit):
    """
    An instance of a Wei unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'wei')


class MWei(Unit):
    """
    An instance of a MWei unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'mwei')


class GWei(Unit):
    """
    An instance of a GWei unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'gwei')


class Szabo(Unit):
    """
    An instance of a Szabo unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'szabo')


class Finney(Unit):
    """
    An instance of a Finney unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'finney')


class Ether(Unit):
    """
    An instance of an Ether unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'ether')


class KEther(Unit):
    """
    An instance of a KEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'kether')


class MEther(Unit):
    """
    An instance of a MEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'mether')


class GEther(Unit):
    """
    An instance of a GEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'gether')


class TEther(Unit):
    """
    An instance of a TEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'tether')
