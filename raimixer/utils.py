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

from typing import Optional

import raimixer.rairpc as rairpc

DONATE_ADDR = 'xrb_3usnd3kirzfudprd3tceauh3sejxpfm754jgnjajbttrefx9obgdqe69wfcf'


# TODO: unittest
def valid_account(acc: str) -> bool:
    if len(acc) != 64:
        return False

    import re

    if not re.match('^xrb_[a-z|0-9]*$', acc):
        return False

    return True


class NormalizeAmountException(Exception):
    pass


# TODO: unittest
def normalize_amount(amount: str, multiplier: int) -> int:
    '''Convert an amount in MRAI or KRAI to RAWs as the RPC interface uses'''

    if ',' in amount:
        raise NormalizeAmountException("Don't use commas in amounts to separate decimals, use a dot")

    if '.' in amount:
        tokens = amount.split('.')
        if len(tokens) > 2:
            raise NormalizeAmountException("Don't use more than one dot for amounts and use them for decimals")

        base, decimal = tokens
        divider = len(decimal)
        amount = amount.replace('.', '')
        return int(amount) * (multiplier // (10 ** divider))

    return int(amount) * multiplier


def consolidate(wallet: str, account: str, rpc: Optional[rairpc.RaiRPC]=None,
                print_func=print):
    if not rpc:
        rpc = rairpc.RaiRPC(account, wallet)
    accounts = rpc.list_accounts()

    for acc in accounts:
        if acc == account:
            continue

        balance = rpc.account_balance(acc)[0]
        if balance > 0:
            print_func(f'{acc} -> {account}')
            rpc.send_and_receive(acc, account, balance)


def delete_empty_accounts(wallet: str, account: str, rpc: Optional[rairpc.RaiRPC]=None,
                          print_func=print):
    if not rpc:
        rpc = rairpc.RaiRPC(account, wallet)
    accounts = rpc.list_accounts()

    for acc in accounts:
        if acc == account:
            continue

        balance = rpc.account_balance(acc)[0]
        if balance == 0:
            print_func(f'Deleting empty account {acc}')
            rpc.delete_account(acc)


