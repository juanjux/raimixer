import string
import random
from pprint import pprint
from typing import List, Dict, Optional


class RaiMixer:
    def __init__(self, orig_account: str, dest_account: str,
            dest_balance: int, orig_balance: int, num_mix_accounts=5, num_rounds=4,
            final_send_from_multiple = False) -> None:

        assert(num_mix_accounts > 1)
        assert(num_rounds > 0)

        self.orig_account = orig_account
        self.dest_account = dest_account
        self.orig_balance = orig_balance
        self.dest_balance = dest_balance
        self.num_mix_accounts = num_mix_accounts
        self.num_rounds = num_rounds
        self.final_send_from_multiple = final_send_from_multiple

        self.mix_accounts: List[str] = []
        self.balances: Dict[str, int] = {}
        self.tx_counter = 0

    def start(self) -> None:
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

    def _generate_accounts(self, num: int) -> List[str]:
        # XXX generate using the RPC
        res: List[str] = []

        while len(res) <= num:
            addr = ''.join(random.choices(string.ascii_lowercase, k=5))
            if addr in res:
                continue
            res.append(addr)

        return res

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
        except:
            self.balances[orig] = orig_balance
            self.balances[dest] = dest_balance
            raise

        print("Sent {} from {} to {}".format(amount, orig, dest))
        pprint(self.balances)

        self._check_balances()
        assert(amount > 0)

    def _check_balances(self):
        total = 0

        for k, v in self.balances.items():
            total += v

        assert(total == self.orig_balance)

    def _mix(self) -> None:
        for acc, balance in self.balances.items():
            if balance > 0:
                mix_plusorig = self.mix_accounts.copy()
                mix_plusorig.append(self.orig_account)
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


def main():
    mixer = RaiMixer('ORIG', 'DEST', 800, 1000, num_mix_accounts=5, num_rounds=2,
                     final_send_from_multiple = True)
    mixer.start()


if __name__ == '__main__':
    main()
