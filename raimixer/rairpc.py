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

import json
import time
from typing import Tuple, List, Dict, Any, Optional

import requests


class RaiRPCException(Exception):
    pass


WAIT_TIMEOUT = 20

# XXX move to utils
MRAI_TO_RAW = 1000000000000000000000000000000
KRAI_TO_RAW = MRAI_TO_RAW // 1000


class RaiRPC:
    def __init__(self, account, wallet, address='[::1]', port='7076') -> None:
        assert(account)
        assert(wallet)

        self.url = 'http://{}:{}'.format(address, port)
        self.account = account
        self.wallet = wallet

    def account_balance(self, account: str) -> Tuple[int, int]:
        res = self._callrpc(action='account_balance', account=account)
        return int(res['balance']), int(res['pending'])

    def create_account(self, representative: Optional[str] = None) -> str:
        account = self._callrpc(action='account_create', wallet=self.wallet)['account']

        if representative:
            self.set_representative(account, representative)

        return account

    def set_representative(self, account, representative):
        self._callrpc(action='account_representative_set', wallet=self.wallet,
                      account=account, representative=representative)

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
        sleep = 0.1
        total_wait = 0.0

        while not finished:
            time.sleep(sleep)
            _, pending = self.account_balance(dest_acc)
            if pending > 0:
                self.receive(dest_acc)

            while not finished:
                time.sleep(sleep)
                total_wait += sleep

                _, pending = self.account_balance(dest_acc)
                if pending == 0:
                    finished = True

                if total_wait > WAIT_TIMEOUT:
                    raise RaiRPCException('Timeout waiting for receive block processing')

            if total_wait > WAIT_TIMEOUT:
                raise RaiRPCException('Timeout waiting for send block')

    def list_accounts(self) -> List[str]:
        return self._callrpc(action='account_list', wallet=self.wallet)['accounts']

    def mrai_to_raw(self, amount_mrai: float) -> int:
        return int(amount_mrai * MRAI_TO_RAW)

    def raw_to_mrai(self, amount_raw: int) -> float:
        return amount_raw / MRAI_TO_RAW

    def wallet_locked(self) -> bool:
        return self._callrpc(action='wallet_locked', wallet=self.wallet)['locked'] == '1'

    def _get_wallet(self) -> str:
        return self._callrpc(action='account_info', account=self.account)['frontier']

    def _get_pending_blocks(self, acc) -> List[str]:
        return self._callrpc(action='pending', account=acc, count=99999)['blocks']

    def _callrpc(self, **kwargs) -> Dict[str, Any]:
        headers = {'content-type': 'application/json'}
        response = requests.post(self.url, data=json.dumps(kwargs).encode(),
                                 headers=headers).json()

        if "error" in response:
            raise RaiRPCException(response['error'])

        return response


if __name__ == '__main__':
    conf_test = json.loads(open("data.json").read())

    wallet = conf_test["wallet"]
    orig_account = conf_test["orig_account"]
    rpc  = RaiRPC(orig_account, wallet)
