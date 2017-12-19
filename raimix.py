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

# Copyright 2017 Juanjo Alvarez

import sys
import random
from pprint import pprint
from typing import List, Dict, Optional

import rairpc

# TODO: rename dest_balance to real_tosend and orig_balance to initial_tosend
# TODO: precalculate the mixin rounds so I can show a nice progress bar of each round
# TODO: read wallet from user directory config
# TODO: Retrieve representatives. Change representative of every created account.
# TODO: kosher Python package


class RaiMixerException(Exception): pass


class RaiMixer:
    def __init__(self, wallet: str, num_mix_accounts=5, num_rounds=4) -> None:

        assert(num_mix_accounts > 1)
        assert(num_rounds > 0)

        self.wallet = wallet
        self.num_mix_accounts = num_mix_accounts
        self.num_rounds = num_rounds

        self.mix_accounts: List[str] = []
        self.balances: Dict[str, int] = {}
        self.tx_counter = 0
        self.rpc: Optional[rairpc.RaiRPC] = None

    def start(self, orig_account: str, dest_account: str, dest_balance: int,
              orig_balance: int, final_send_from_multiple = False) -> None:

        if type(dest_balance) != int or type(orig_balance) != int:
                raise RaiMixerException('dest_balance and orig_balance must be integers')

        self.orig_account = orig_account
        self.dest_account = dest_account
        self.orig_balance = orig_balance
        self.dest_balance = dest_balance
        self.final_send_from_multiple = final_send_from_multiple

        self.rpc = rairpc.RaiRPC(self.orig_account, self.wallet)
        self.mix_accounts = self._generate_accounts(self.num_mix_accounts)

        self._load_balances()

        # Choose the first accounts to receive funds
        num_first_dests = random.randrange(2, len(self.mix_accounts) + 1)
        first_dests = random.choices(self.mix_accounts, k=num_first_dests)

        print('\nStarting sending to initial mixing accounts...')
        self._send_one_to_many(self.orig_account, first_dests)

        # Shake it!
        for i in range(self.num_rounds):
            print('\nStarting mixing round %d...' % (i + 1))
            self._mix()

        self._send_to_dest()

        print('\nDone! Total transactions done: %d' % self.tx_counter)
        assert(self.balances[self.orig_account] == self.orig_balance - self.dest_balance)
        assert(self.balances[self.dest_account] == self.dest_balance)

        self._delete_accounts()

    def _generate_accounts(self, num: int) -> List[str]:
        print('\nCreating mixing accounts...')
        res = [self.rpc.create_account() for n in range(num)]
        return res

    def _delete_accounts(self):
        for acc in self.mix_accounts:
            assert(self.rpc.account_balance(acc) == 0)
            self.rpc.delete_account(acc)

    def _load_balances(self) -> None:
        for acc in self.mix_accounts:
            self.balances[acc] = 0

        self.balances[self.orig_account] = self.orig_balance
        self.balances[self.dest_account] = 0

    def _send_one_to_many(self, from_: str, dests: List[str],
                          max_send: Optional[int] = None) -> None:
        # from_ could be in dests. This is not a bug but allows for letting some
        # amount in the from_ account if the caller want that to happen (like when mixing)

        split = self._random_amounts_split(self.balances[from_], len(dests))

        for idx, am in enumerate(split):
            if am > 0 and dests[idx] != from_:
                self._send(from_, dests[idx], am)

    def _send_many_to_one(self, froms: List[str], dest: str,
                          max_send: Optional[int] = None) -> None:
        already_sent = 0

        for acc in froms:
            balance = self.balances[acc]

            if acc == dest or balance == 0:
                continue

            tosend: int = 0
            if max_send is not None and (already_sent + balance > max_send):
                tosend = max_send - already_sent
            else:
                tosend = balance

            self._send(acc, dest, tosend)
            already_sent += tosend

            if max_send is not None:
                assert(already_sent <= max_send)
                if already_sent == max_send:
                    return

    def _send(self, orig: str, dest: str, amount: int) -> None:
        orig_balance = self.balances[orig]
        dest_balance = self.balances[dest]

        assert(amount <= orig_balance)

        try:
            self.balances[orig] -= amount
            self.balances[dest] += amount
            self.tx_counter += 1
            self.rpc.send_and_receive(orig, dest, amount)
        except:
            self.balances[orig] = orig_balance
            self.balances[dest] = dest_balance
            self.tx_counter -= 1
            raise

        print("Sent {} from {} to {}".format(amount, orig, dest))
        # pprint(self.balances)

        self._check_balances()
        assert(amount > 0)

    def _check_balances(self):
        total = 0

        for k, v in self.balances.items():
            total += v

        assert(total == self.orig_balance)

    def _mix(self) -> None:
        mix_plusorig = self.mix_accounts.copy() + [self.orig_account]

        for acc, balance in self.balances.items():
            if balance > 0:
                self._send_one_to_many(acc, mix_plusorig)

    def _send_to_dest(self) -> None:
        # Move any balance in the orig account into one of the mixer accounts
        if self.balances[self.orig_account] > 0:
            print('\nMoving remaining balance in the orig account to mix accounts...')
            self._send_one_to_many(self.orig_account, self.mix_accounts)

        if not self.final_send_from_multiple:
            # Choose a single non-origin account to sent from, collect
            # all the balances to it
            send_from_acc = random.choice(self.mix_accounts)
            print('\nSending to final carrier account [%s]...' % send_from_acc)

            for acc, balance in self.balances.items():
                if acc == send_from_acc:
                    continue

                if balance > 0:
                    self._send(acc, send_from_acc, balance)

        print('\nSending to destination account...')
        self._send_many_to_one(self.mix_accounts + [self.orig_account],
                               self.dest_account, self.dest_balance)

        # Send the rest back to the orig account
        print('\nSending remaining balance back to the orig account...')
        self._send_many_to_one(self.mix_accounts, self.orig_account)

    def _random_amounts_split(self, total: int, num_accounts: int) -> List[int]:
        # loop calculating a random amount from 0 to 1/3 of the remainder until
        # the pending amount is 1/10, then send that to a random account
        tosend: Dict[int, int] = {}
        for a in range(num_accounts):
            tosend[a] = 0

        remaining = total

        while True:
            amount = random.randint(1, max(remaining // num_accounts, 1))
            dest = random.randrange(0, num_accounts)
            tosend[dest] += amount
            remaining -= amount

            if remaining == 0:
                break

            if remaining < total / len(self.mix_accounts):
                tosend[dest] += remaining
                break

        return [tosend[i] for i in tosend.keys()]


def parse_options():
    from argparse import ArgumentParser

    # FIXME: better description...
    parser = ArgumentParser(description='Mix amounts before sending')
    parser.add_argument('-w', '--wallet', help='User wallet ID', required=True)
    parser.add_argument('-s', '--source_acc', help='Source account', required=True)
    parser.add_argument('-d', '--dest_acc', help='Destination account')
    parser.add_argument('-c', '--clean', action='store_true', default=False,
            help='Move everything to the source account. Useful after node crashes.')
    parser.add_argument('-a', '--amount',
            help='Amount. Use m, k prefixes for mega/kilo rai')
    parser.add_argument('-i', '--initial_amount',
            help='Initial amount to mix. Helps masking transactions. Must be greater\n'
                 'than --amount. Rest will be returned to source account')
    parser.add_argument('-m', '--dest_from_multiple', action='store_true', default=False,
            help='Send to the final destination from various mixing account')
    parser.add_argument('-n', '--num_mixers', type=int, default=4,
            help='Number of mixing accounts to create (default=4)')
    parser.add_argument('-r', '--num_rounds', type=int, default=2,
            help='Number of mixing rounds to do (default=2')

    return parser.parse_args()


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


def convert_amount(amount):
    if not amount:
        print('--amount option missing')
        sys.exit(1)

    amount_unit = amount[-1]

    if '.' in amount or ',' in amount:
        print('Amount units must be integers')
        sys.exit(1)

    if amount_unit not in ['k', 'K', 'm', 'M'] or '.' in amount or ',' in amount:
        print('Amount options must end in m (megarai) or k (kilorai) and must be integers')
        sys.exit(1)

    real_amount = amount[:-1]

    if amount_unit.lower() == 'k':
        return int(real_amount) * rairpc.KRAI_TO_RAW

    if amount_unit.lower() == 'm':
        return int(real_amount) * rairpc.MRAI_TO_RAW


def main():
    options = parse_options()
    if options.clean:
        clean(options.wallet, options.source_acc)
        sys.exit(0)

    if not options.wallet:
        print('--wallet option is mandatory')
        sys.exit(1)

    if not options.source_acc or not options.dest_acc:
        print('--source_acc and --dest_acc are mandatory')
        sys.exit(1)

    if not options.amount:
        print('--amount is mandatory')
        sys.exit(1)

    send_amount = convert_amount(options.amount)

    if options.initial_amount:
        start_amount = convert_amount(options.initial_amount)
    else:
        start_amount = send_amount

    mixer = RaiMixer(options.wallet, num_mix_accounts=options.num_mixers,
                     num_rounds=options.num_rounds)

    mixer.start(options.source_acc, options.dest_acc, send_amount,
                start_amount, final_send_from_multiple=options.dest_from_multiple)


if __name__ == '__main__':
    main()
