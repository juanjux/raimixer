import raimixer.rairpc as rairpc
from raimixer.raimixer import RaiMixer, WalletLockedException

import sys
from textwrap import dedent
from typing import Dict, Any


def parse_options(raiconfig: Dict[str, Any]) -> Any:
    from argparse import ArgumentParser, RawTextHelpFormatter

    parser = ArgumentParser(description=dedent(
        '''
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

        xrb_3usnd3kirzfudprd3tceauh3sejxpfm754jgnjajbttrefx9obgdqe69wfcf

        (Thank you!❤)
        '''
        ), formatter_class=RawTextHelpFormatter)

    parser.add_argument('dest_acc', type=str, nargs='?',
        help='Destination account (mandatory except on --clean)')

    parser.add_argument('amount', type=str, nargs='?',
        help='Amount. Use xrb/mrai or krai sufixes for mega/kilo rai (mandatory except for --clean)')

    parser.add_argument('-w', '--wallet', type=str, default=raiconfig['wallet'],
        help='User wallet ID (default: from Rai config)')

    parser.add_argument('-s', '--source_acc', type=str, default=raiconfig['default_account'],
        help='Source account (default: from Rai config)')

    parser.add_argument('-c', '--clean', action='store_true', default=False,
        help='Move everything to the source account. Useful after node crashes.')

    parser.add_argument('-i', '--initial_amount', type=str,
        help='Initial amount to mix. Helps masking transactions. Must be greater\n'
        'than "amount". Rest will be returned to source account (default: equal to "amount")')

    parser.add_argument('-m', '--dest_from_multiple', action='store_true', default=False,
        help='Send to the final destination from various mixing account')

    parser.add_argument('-n', '--num_mixers', type=int, default=4,
        help='Number of mixing accounts to create (default=4)')

    parser.add_argument('-r', '--num_rounds', type=int, default=2,
        help='Number of mixing rounds to do (default=2')

    parser.add_argument('-u', '--rpc_address', type=str, default=raiconfig['rpc_address'],
        help='RPC address (default: from Rai config)')

    parser.add_argument('-p', '--rpc_port', type=str, default=raiconfig['rpc_port'],
        help='RPC port (default: from Rai config)')

    options = parser.parse_args()

    if options.clean:
        options.dest_acc = 'foo'
        options.amount = 'foo'

    if not options.dest_acc:
        print('"dest_acc" option is mandatory')
        parser.print_help()
        sys.exit(1)

    if not options.amount:
        print('"amount" option is mandatory')
        parser.print_help()
        sys.exit(1)

    return options


def clean(wallet, account):
    rpc = rairpc.RaiRPC(account, wallet)
    accounts = rpc.list_accounts()

    for acc in accounts:
        if acc == account:
            continue

        balance = rpc.account_balance(acc)[0]
        if balance > 0:
            print(balance)
            print('%s -> %s' % (acc, account))
            rpc.send_and_receive(acc, account, balance)


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


def normalize_amount(amount: str, multiplier: int) -> int:
    if ',' in amount:
        print("Don't use commas in amounts to separate decimals, use a dot")
        print_amount_help()
        sys.exit(1)

    if '.' in amount:
        tokens = amount.split('.')
        if len(tokens) > 2:
            print("Don't use more than one dot for amounts and use them for decimals")
            print_amount_help()
            sys.exit(1)

        base, decimal = tokens
        divider = len(decimal)
        amount = amount.replace('.', '')
        return int(amount) * (multiplier // (10 ** divider))

    return int(amount) * multiplier


def convert_amount(amount):
    amount = amount.lower()
    raw_amount: int = ''

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

    return raw_amount


def main():
    from raimixer.read_raiconfig import get_raiblocks_config
    from requests.exceptions import ConnectionError

    raiconfig = get_raiblocks_config()
    options = parse_options(raiconfig)

    try:
        if options.clean:
            clean(options.wallet, options.source_acc)
            sys.exit(0)

        if '::1' in options.rpc_address:
            options.rpc_address = options.rpc_address.replace('::1', '[::1]')

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
                    start_amount, options.dest_from_multiple,
                    raiconfig['representatives'])
    except ConnectionError:
        print('Error: could not connect to the node, is the wallet running and '
              'unlocked?')
        sys.exit(1)
    except WalletLockedException:
        print('Error: wallet is locked. Please unlock it before using this')
        sys.exit(1)


if __name__ == '__main__':
    main()
