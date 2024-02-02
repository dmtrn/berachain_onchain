from utils.miscellaneous.create_files import create_files
import os
import sys
import asyncio
import logging
import getpass

from libs.pretty_utils.miscellaneous.inputting import timeout_input
from data import config
from functions.Import import Import
from functions.activity import activity
from utils.encryption import get_cipher_suite
from data.config import SALT_PATH, CIPHER_SUITE
from data.models import ProgramActions, Settings


def check_encrypt_param(settings):
    if settings.use_private_key_encryption:
        if not os.path.exists(SALT_PATH):
            print(f'You need to add salt.dat to {SALT_PATH} for correct decryption of private keys!\n'
                  f'After the program has started successfully, you can delete this file. \n\n'
                  f'If you do not need encryption, please change use_private_key_encryption to False.')
            sys.exit(1)
        with open(SALT_PATH, 'rb') as f:
            salt = f.read()
        user_password = getpass.getpass('[DECRYPTOR] Write here you password '
                                        '(the field will be hidden): ').strip().encode()
        CIPHER_SUITE.append(get_cipher_suite(user_password, salt))


async def start_script():
    await asyncio.wait([asyncio.create_task(activity())])


if __name__ == '__main__':
    create_files()
    main_settings = Settings()
    check_encrypt_param(main_settings)

    while True:
        action = None
        print('''  Select the action:
1) Import wallets from the spreadsheet to the DB;
2) Start Activity on Bera; 
''')

        try:
            action = int(timeout_input('🐻>>> ', 60, '2'))
            loop = asyncio.get_event_loop()
            if action == ProgramActions.ImportWallets.Selection:
                loop.run_until_complete(Import.wallets())
            elif action == ProgramActions.StartScript.Selection:
                loop.run_until_complete(start_script())
            else:
                break

        except KeyboardInterrupt:
            print()

        except ValueError as err:
            print(f"{config.RED}Value error: {err}{config.RESET_ALL}")

        except BaseException as e:
            logging.exception('main')
            print(f'\n{config.RED}Something went wrong: {e}{config.RESET_ALL}\n')

        if action:
            break
