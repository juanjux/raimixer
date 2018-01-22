# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Copyright 2017-2018 Juanjo Alvarez

import raimixer.rairpc as rairpc
from raimixer.raimixer import RaiMixer, WalletLockedException
from raimixer.utils import (normalize_amount, NormalizeAmountException, DONATE_ADDR,
                           consolidate, delete_empty_accounts)

import sys
from textwrap import dedent
from typing import Dict, Any

HAS_GUI = True
try:
    import raimixer.gui
except ImportError as e:
    print(e)
    HAS_GUI = False


def parse_options(raiconfig: Dict[str, Any]) -> Any:
    from argparse import ArgumentParser, RawTextHelpFormatter

    parser = ArgumentParser(description=dedent(
        f'''
         ____       _ __  __ _
        |  _ \ __ _(_)  \/  (_)_  _____ _ __
        | |_) / _` | | |\/| | \ \/ / _ \ '__|
        |  _ < (_| | | |  | | |>  <  __/ |
        |_| \_\__,_|_|_|  |_|_/_/\_\___|_|

        Mix/scramble RaiBlocks transactions between random local accounts before
        sending to the real destination.

        Example usage:

        raimixer xrb_3zq1yrhgij8ix35yf1khehzwfiz9ojjotndtqprpyymixxwxnkhn44qgqmy5 10xrb

        If this software is useful to you, consider donating to the author's rai-funds!

        {DONATE_ADDR}

        (Thank you!❤)
        '''
        ), formatter_class=RawTextHelpFormatter)

    parser.add_argument('dest_acc', type=str, nargs='?',
        help='Destination account (mandatory except on --consolidate)')

    parser.add_argument('amount', type=str, nargs='?',
        help='Amount. Use xrb/mrai or krai sufixes for mega/kilo rai (mandatory except for --consolidate)')

    parser.add_argument('-w', '--wallet', type=str, default=raiconfig['wallet'],
        help='User wallet ID (default: from Rai config)')

    parser.add_argument('-s', '--source_acc', type=str, default=raiconfig['default_account'],
        help='Source account (default: from Rai config)')

    parser.add_argument('-c', '--consolidate', action='store_true', default=False,
        help='Move everything to the source account. Useful after node crashes.')

    parser.add_argument('-d', '--delete_empty', action='store_true', default=False,
        help='Delete empty accounts')

    parser.add_argument('-i', '--initial_amount', type=str,
        help='Initial amount to mix. Helps masking transactions. Must be greater\n'
        'than "amount". Rest will be returned to source account (default: equal to "amount")')

    parser.add_argument('-m', '--dest_from_multiple', action='store_true', default=False,
        help='Send to the final destination from various mixing account')

    parser.add_argument('-l', '--leave_remainder', action='store_true', default=False,
        help="Leave excess amount in the mixing accounts (don't return to main account at the end)")

    parser.add_argument('-n', '--num_mixers', type=int, default=4,
        help='Number of mixing accounts to create (default=4)')

    parser.add_argument('-r', '--num_rounds', type=int, default=2,
        help='Number of mixing rounds to do (default=2')

    parser.add_argument('-u', '--rpc_address', type=str, default=raiconfig['rpc_address'],
        help='RPC address (default: from Rai config)')

    parser.add_argument('-p', '--rpc_port', type=str, default=raiconfig['rpc_port'],
        help='RPC port (default: from Rai config)')

    parser.add_argument('-g', '--gui', action='store_true', default=False,
        help='Start the GUI (needs PyQt5 correctly installed)')

    options = parser.parse_args()

    if options.consolidate:
        options.dest_acc = 'foo'
        options.amount = 'foo'

    if not options.gui:
        if not options.dest_acc:
            print('"dest_acc" option is mandatory')
            parser.print_help()
            sys.exit(1)

        if not options.amount:
            print('"amount" option is mandatory')
            parser.print_help()
            sys.exit(1)

    if not options.rpc_address.startswith('['):
        options.rpc_address = '[' + options.rpc_address
        if not options.rpc_address.endswith(']'):
            options.rpc_address = options.rpc_address + ']'

    return options


def print_amount_help() -> None:
    print(dedent('''
    Help on amounts:

    Amounts must have the format <number><unit>. Numbers can be integers or
    decimals (always using a dot to separe decimals, don't use a comma and don't
    use thousands separators).

    <unit> must be one of xrb/mrai (equivalent) or krai.
    1 mrai or xrb = 1.000 krai. 1 krai = 1.000 rai.

    Good:

    0.9xrb
    10.20XRB
    900.23krai

    Bad:

    0,9xrb (don't use commas)
    10 xrb (don't use spaces between the amount and the unit)
    10.123.122krai (don't use thousand separators)
    '''))


def convert_amount(amount):
    amount = amount.lower()
    raw_amount: int = ''

    try:
        if amount.endswith('xrb'):
            raw_amount = normalize_amount(amount[:-3], rairpc.MRAI_TO_RAW)
        elif amount.endswith('mrai'):
            raw_amount = normalize_amount(amount[:-4], rairpc.MRAI_TO_RAW)
        elif amount.endswith('krai'):
            raw_amount = normalize_amount(amount[:-4], rairpc.KRAI_TO_RAW)
        else:
            print('Amount options must end in mrai/xrb (XRB/megarai) or krai (kilorai)')
            print_amount_help()
            sys.exit(1)
    except NormalizeAmountException as e:
        print(str(e))
        print_amount_help()
        sys.exit(1)

    return raw_amount


def main():
    from raimixer.config import get_raiblocks_config
    from requests.exceptions import ConnectionError

    raiconfig = get_raiblocks_config()
    options = parse_options(raiconfig)

    global HAS_GUI
    if options.gui:
        if not HAS_GUI:
            print('Error: --gui requested but GUI cannot be started (check PyQt5 '
                  'is correctly installed')
            sys.exit(1)

        main_gui(raiconfig, options)
        sys.exit(0)
    else:
        HAS_GUI = False

    try:
        if options.consolidate:
            consolidate(options.wallet, options.source_acc)

        if options.delete_empty:
            delete_empty_accounts(options.wallet, options.source_acc)

        if options.consolidate or options.delete_empty:
            sys.exit(0)

        rpc = rairpc.RaiRPC(options.source_acc, options.wallet,
                            options.rpc_address, options.rpc_port)

        send_amount = convert_amount(options.amount)
        if options.initial_amount:
            start_amount = convert_amount(options.initial_amount)
        else:
            start_amount = send_amount

        mixer = RaiMixer(options.wallet, options.num_mixers,
                         options.num_rounds, rpc)

        mixer.start(options.source_acc, options.dest_acc, send_amount,
                    start_amount, options.dest_from_multiple, options.leave_remainder,
                    raiconfig['representatives'])
    except ConnectionError:
        print('Error: could not connect to the node, is the wallet running and '
              'unlocked?')
        sys.exit(1)
    except WalletLockedException:
        print('Error: wallet is locked. Please unlock it before using this')
        sys.exit(1)


def main_gui(raiconfig, options):
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    gui = raimixer.gui.RaimixerGUI(options, raiconfig)
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
