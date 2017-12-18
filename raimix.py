import random
from pprint import pprint
from typing import List, Dict, Optional

ORIG_ACCOUNT = 'ORIG'
ORIG_BALANCE = 10
DEST_BALANCE = 8
DEST_ACCOUNT = 'DEST'
MIX_ACCOUNTS: List[str] = ['A', 'B', 'C', 'D', 'E']
NUM_ROUNDS = 3
FINAL_SENT_FROM_MULTIPLE = True

# TODO: Sent more than needed to the mixing accounts so it's harder
# to track based on the exact amount received by the destination. This balance
# would be returned at the end.


def load_balances() -> Dict[str, int]:
    balances: Dict[str, int] = {}

    for acc in MIX_ACCOUNTS:
        balances[acc] = 0

    balances[ORIG_ACCOUNT] = ORIG_BALANCE
    balances[DEST_ACCOUNT] = 0

    return balances


def check_balances(balances: Dict[str, int]) -> None:
    total = 0

    for k, v in balances.items():
        total += v

    assert(total == ORIG_BALANCE)


def send(balances, orig: str, dest: str, amount: int) -> None:
    orig_balance = balances[orig]
    dest_balance = balances[dest]

    assert(amount <= orig_balance)

    try:
        balances[orig] -= amount
        balances[dest] += amount
    except:
        balances[orig] = orig_balance
        balances[dest] = dest_balance
        raise

    print("Sent {} from {} to {}".format(amount, orig, dest))
    pprint(balances)

    check_balances(balances)
    assert(amount > 0)


def random_amounts_split(total: int, num_accounts: int) -> List[int]:
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

        if remaining < total / len(MIX_ACCOUNTS):
            tosend[dest] += remaining
            break

    return [tosend[i] for i in tosend.keys()]


def mix(balances: Dict[str, int]) -> None:
    for acc, balance in balances.items():
        if balance > 0:
            mix_plusorig = MIX_ACCOUNTS.copy()
            mix_plusorig.append(ORIG_ACCOUNT)

            send_one_to_many(balances, acc, mix_plusorig)


def send_to_dest(balances: Dict[str, int]) -> None:
    remaining_tosend = DEST_BALANCE

    # Move any balance in the orig account into one of the mixer accounts
    if balances[ORIG_ACCOUNT] > 0:
        print('\nMoving remaining balance in the orig account to mix accounts...')
        send_one_to_many(balances, ORIG_ACCOUNT, MIX_ACCOUNTS)

    if not FINAL_SENT_FROM_MULTIPLE:
        # Choose a single non-origin account to sent from, collect
        # all the balances to it
        send_from_acc = random.choice(MIX_ACCOUNTS)
        print('\nSending to final carrier account [%s]...' % send_from_acc)

        for acc, balance in balances.items():
            if acc == send_from_acc:
                continue

            if balance > 0:
                send(balances, acc, send_from_acc, balance)

    print('\nSending to destination account...')
    send_many_to_one(balances, MIX_ACCOUNTS + [ORIG_ACCOUNT], DEST_ACCOUNT, DEST_BALANCE)

    # Send the rest back to the orig account
    print('\nSending remaining balance back to the orig account...')
    send_many_to_one(balances, MIX_ACCOUNTS, ORIG_ACCOUNT)


def send_one_to_many(balances: Dict[str, int], from_: str, dests: List[str]) -> None:
    # from_ could be in dests. This is not a bug but allows for letting some
    # amount in the from_ account if the caller want that to happen (like when mixing)

    split = random_amounts_split(balances[from_], len(dests))

    for idx, am in enumerate(split):
        if am > 0 and dests[idx] != from_:
            send(balances, from_, dests[idx], am)


def send_many_to_one(balances: Dict[str, int], froms: List[str], dest: str,
        max_send: Optional[int] = None) -> None:

    already_sent = 0

    for acc in froms:
        balance = balances[acc]

        if acc == dest or balance == 0:
            continue

        tosend: int = 0
        if max_send is not None and (already_sent + balance > max_send):
            tosend = max_send - already_sent
        else:
            tosend = balance

        send(balances, acc, dest, tosend)
        already_sent += tosend

        if max_send is not None:
            assert(already_sent <= max_send)
            if already_sent == max_send:
                return


def main():
    balances = load_balances()

    # Choose the first accounts to receive funds
    num_first_dests = random.randrange(2, len(MIX_ACCOUNTS) + 1)
    first_dests = random.choices(MIX_ACCOUNTS, k=num_first_dests)
    print('\nStarting sending to initial mixing accounts...')
    send_one_to_many(balances, ORIG_ACCOUNT, first_dests)

    # Shake it!
    for i in range(NUM_ROUNDS):
        print('\nStarting mixing round %d...' % (i + 1))
        mix(balances)

    send_to_dest(balances)
    assert(balances[ORIG_ACCOUNT] == ORIG_BALANCE - DEST_BALANCE)
    assert(balances[DEST_ACCOUNT] == DEST_BALANCE)


if __name__ == '__main__':
    main()
