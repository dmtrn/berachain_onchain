import time
from typing import Optional

from libs.pretty_utils.type_functions.dicts import update_dict
from libs.pretty_utils.miscellaneous.files import touch, write_json, read_json

from data import config
from utils.miscellaneous.create_spreadsheet import create_spreadsheet


def create_files():
    touch(path=config.FILES_DIR)
    create_spreadsheet(path=config.IMPORT_FILE, headers=('private_key', 'name', 'proxy'),
                       sheet_name='Wallets')

    try:
        current_settings: Optional[dict] = read_json(path=config.SETTINGS_FILE)

    except:
        current_settings = {}

    settings = {
        'use_private_key_encryption': False,
        'maximum_gas_price': 30,
        'oklink_api_key': '',
        'usd_threshold': 0.1,
        'networks': {
            # Добавляем пул рпц для актуальной сети
            'Scroll': {'rpcs': ['https://rpc.scroll.io']},
            # Сети для мостов
            # 'ethereum': {'rpc': 'https://rpc.ankr.com/eth/', 'api_key': ''}
        },
        'okx': {
            'required_minimum_balance': 0.006,
            'withdraw_amount': {'from': 0.006, 'to': 0.007},
            'delay_between_withdrawals': {'from': 1200, 'to': 1500},
            'credentials': {
                'api_key': '',
                'secret_key': '',
                'passphrase': '',
            }
        },
        'binance': {
            'required_minimum_balance': 0.006,
            'withdraw_amount': {'from': 0.006, 'to': 0.007},
            'delay_between_withdrawals': {'from': 1200, 'to': 1500},
            'credentials': {
                'api_key': '',
                'secret_key': '',
            }
        },
        'txs_after_timestamp': 1684368000,
        'okx_withdrawls_timestamp': int(time.time()),
        'minimal_balance': 0.002,
        'use_official_bridge': False,
        'pre_initial_actions_delay': {'from': 180, 'to': 240},
        'initial_actions_delay': {'from': 3600, 'to': 7200},
        'amount_to_bridge': {'from': 0.008, 'to': 0.00905},
        'swaps': {'from': 1, 'to': 3},
        'liquidity': {'from': 1, 'to': 3},
        'lending': {'from': 1, 'to': 3},
        'dmail': {'from': 3, 'to': 10},
        'liquidity_holding_time': 7 * (24 * 60 * 60),
        'mint_nft': {'from': 1, 'to': 10},
        'paid_nft': False,
        'activity_actions_delay': {'from': 259200, 'to': 345600},
        'eth_amount_for_bridge': {'from': 0.008, 'to': 0.0086},
        'eth_amount_for_swap': {'from': 0.0007, 'to': 0.0015},
        'eth_amount_for_liquidity': {'from': 0.0007, 'to': 0.0015},
        "dest_chain_fee": {"from": 0.00025,"to": 0.00033},
        'available_networks': {
            'Linea': False,
            'Arbitrum One': True,
            'Base': False,
            'Optimism': True
        }
    }
    write_json(path=config.SETTINGS_FILE, obj=update_dict(modifiable=current_settings, template=settings), indent=2)


create_files()