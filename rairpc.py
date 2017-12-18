import json
import time
from pprint import pprint
from typing import Tuple, List, Dict, Any

import requests

class RaiRPCException(Exception): pass

# TODO: Retrieve representatives. Change representative of every created account.

WAIT_TIMEOUT = 20
MRAI_TO_RAW = 1000000000000000000000000000000

class RaiRPC:
    def __init__(self, account, wallet, address='[::1]', port='7076'):
        assert(account)
        assert(wallet)

        self.url = 'http://{}:{}'.format(address, port)
        self.account = account
        self.wallet = wallet

    def account_balance(self, account: str) -> Tuple[int, int]:
        res = self._callrpc(action='account_balance', account=account)
        return int(res['balance']), int(res['pending'])

    def create_account(self) -> str:
        res = self._callrpc(action='account_create', wallet=self.wallet)
        return res['account']

    def delete_account(self, account: str) -> bool:
        res = self._callrpc(action='account_remove', wallet=self.wallet, account=account)
        return bool(res['removed'])

    def send(self, source_acc: str, dest_acc: str, amount: int) -> str:
        assert(amount > 0)

        res = self._callrpc(action='send', wallet=self.wallet, source=source_acc,
                            destination=dest_acc, amount=amount)
        return res['block']

    def receive(self, dest_acc: str) -> None:
        blocks = self._get_pending_blocks(dest_acc)

        for recv_block in blocks:
            self._callrpc(action='receive', wallet=self.wallet, account=dest_acc,
                          block=recv_block)

    def send_and_receive(self, source_acc: str, dest_acc: str, amount: int) -> None:
        self.send(source_acc, dest_acc, amount)

        finished = False
        sleep = 1.0
        total_wait = 0.0

        while not finished:
            time.sleep(sleep)
            print('DEBUG Waiting for the POW and receive block to show on the network...')
            _, pending = self.account_balance(dest_acc)
            if pending > 0:
                self.receive(dest_acc)

            while not finished:
                print('DEBUG Waiting for the POW of the send block to finish...')
                time.sleep(sleep)
                total_wait += sleep

                _, pending = self.account_balance(dest_acc)
                if pending == 0:
                    finished = True

                if total_wait > WAIT_TIMEOUT:
                    raise RaiRPCException('Timeout waiting for receive block processing')

            if total_wait > WAIT_TIMEOUT:
                raise RaiRPCException('Timeout waiting for send block')

    def mrai_to_raw(self, amount_mrai: float) -> int:
        return int(amount_mrai * MRAI_TO_RAW)

    def raw_to_mrai(self, amount_raw: int) -> float:
        return amount_raw / MRAI_TO_RAW

    def _get_wallet(self) -> str:
        return self._callrpc(action='account_info', account=self.account)['frontier']

    def _get_pending_blocks(self, acc) -> List[str]:
        return self._callrpc(action='pending', account=acc, count=99999)['blocks']

    def _callrpc(self, **kwargs) -> Dict[str, Any]:
        headers = {'content-type': 'application/json'}
        response = requests.post(self.url, data=json.dumps(kwargs), headers=headers).json()

        if "error" in response:
            raise RaiRPCException(response['error'])

        return response


if __name__ == '__main__':
    conf_test = json.loads(open("data.json").read())
    orig_account = conf_test["orig_account"]
    second_account = conf_test["second_account"]
    wallet = conf_test["wallet"]

    rpc = RaiRPC(orig_account, wallet)
    print("BALANCE ORIG: ", rpc.account_balance(orig_account))
    print("BALANCE DEST: ", rpc.account_balance(second_account))

    tstart = time.time()
    AMOUNT = rpc.mrai_to_raw(0.1)
    # rpc.send_and_receive(orig_account, second_account, AMOUNT)
    rpc.send_and_receive(second_account, orig_account, AMOUNT)
    elapsed = time.time() - tstart
    print("BALANCE ORIG: ", rpc.account_balance(orig_account))
    print("BALANCE DEST: ", rpc.account_balance(second_account))
    print("Elapsed time: {}".format(elapsed))
