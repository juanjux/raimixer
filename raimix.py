import random
from pprint import pprint
from typing import List, Dict

ORIG_ACCONT = 'ORIG'
ORIG_BALANCE = 10
DEST_BALANCE = 8
DEST_ACCOUNT = 'DEST'
MIX_ACCOUNTS: List[str] = ['A', 'B', 'C', 'D', 'E']
NUM_ROUNDS = 4


def load_balances() -> Dict[str, int]:
    balances: Dict[str, int] = {}

    for acc in MIX_ACCOUNTS:
        balances[acc] = 0

    balances[ORIG_ACCONT] = ORIG_BALANCE
    balances[DEST_ACCOUNT] = 0

    return balances


def check_balances(balances: Dict[str, int]) -> None:
    total = 0

    for k,v in balances.items():
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

        if remaining < total / 10:
            tosend[dest] += remaining
            break

    return [tosend[i] for i in tosend.keys()]


def mix(balances: Dict[str, int]) -> None:
    pass


def main():
    balances = load_balances()

    # Choose the first accounts to receive funds
    num_first_dests = random.randrange(2, len(MIX_ACCOUNTS) + 1)
    first_dests = random.choices(MIX_ACCOUNTS, k=num_first_dests)
    print("First destinations: ", first_dests)

    # Send the funds to the choosen accounts, in random amounts
    split = random_amounts_split(ORIG_BALANCE, len(first_dests))

    print('Starting sending to initial mixing accounts...')
    for idx, am in enumerate(split):
        send(balances, ORIG_ACCONT, first_dests[idx], am)

    done_rounds = 0
    while done_rounds <= NUM_ROUNDS:
        mix(balances)

if __name__ == '__main__':
      main()
