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

from typing import Dict, List

from raimixer.raimixer import RaiMixer
from raimixer.config import read_raimixer_config, write_raimixer_config
from raimixer.rairpc import RaiRPC, MRAI_TO_RAW, KRAI_TO_RAW
from raimixer.utils import consolidate, delete_empty_accounts

from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
        QGroupBox, QLabel, QLineEdit, QSpinBox, QComboBox, QTextBrowser,
        QCheckBox, QMainWindow, QMessageBox
)
from PyQt5.QtGui import QFont, QFontMetrics, QTextCursor
from PyQt5.QtCore import pyqtSignal, QTimer, QThread
from requests import ConnectionError

# TODO: checkbox "randomly use balance from all accounts"
# TODO: checkbox "use all" next to "amount to increase"
# TODO: remove the mixing settings in the main GUI
# TODO: progress bar
# TODO: tooltips
# TODO: move the settings and the wrappers to another file, move all under gui/ dir

MRAI_TEXT = 'XRB/MRAI'
KRAI_TEXT = 'KRAI'


def _unit_combo():
    unit_combo = QComboBox()
    unit_combo.addItem(MRAI_TEXT)
    unit_combo.addItem(KRAI_TEXT)
    return unit_combo


class RaimixerGUI(QMainWindow):

    def __init__(self, options, raiconfig, parent=None):
        super().__init__(parent)
        self.options                  = options
        self.raiconfig                = raiconfig
        self.rpc                      = None  # updated on update_wallet_conn
        self.accounts_loaded          = False
        self.wallet_connected         = False
        self.wallet_locked            = True
        self.accounts: Dict[str, int] = {}
        self.config_window            = ConfigWindow(options, self)

        self.config_window.reset_values()
        self.initUI()

    def initUI(self):
        central_wid = QWidget(self)
        self.setCentralWidget(central_wid)

        self.main_layout = QVBoxLayout()
        central_wid.setLayout(self.main_layout)

        self.create_accounts_box()

        self.mixwallet_layout = QHBoxLayout()
        self.create_mix_box()
        self.create_walletstatus_box()
        self.main_layout.addLayout(self.mixwallet_layout)

        self.create_consolidate_box()

        self.create_buttons_box()
        self.create_log_box()

        self.setWindowTitle('RaiMixer')

        # Timer to check & update the connection status to the wallet
        self.wallet_conn_timer = QTimer(self)
        self.wallet_conn_timer.timeout.connect(self.update_wallet_conn)
        self.wallet_conn_timer.start(1000)

    def _update_accounts(self):
        if not self.rpc:
            return

        self.accounts.clear()
        all_accounts = self.rpc.list_accounts()
        for acc in all_accounts:
            self.accounts[acc] = self.rpc.account_balance(acc)

    def _get_selected_account(self):
        selected = self.source_combo.currentText()
        return selected.split(' ')[0] if ' ' in selected else selected

    def _get_divider(self) -> int:
        return MRAI_TO_RAW if self.unit_combo.currentText() == MRAI_TEXT else KRAI_TO_RAW

    def _update_accounts_combo(self):
        scombo   = self.source_combo
        divider  = self._get_divider()
        selected = self._get_selected_account()

        scombo.clear()
        selected_text = ''
        for acc, balance in self.accounts.items():
            balance = self.accounts[acc][0] / divider
            text = f'{acc} ({balance})'
            scombo.addItem(text)
            if acc == selected:
                selected_text = text

        scombo.setCurrentText(selected_text)

    def update_wallet_conn(self):
        self.rpc = RaiRPC(self.source_combo.currentText(), self.raiconfig['wallet'],
                     self.options.rpc_address, self.options.rpc_port)

        try:
            self.wallet_locked = self.rpc.wallet_locked()
        except ConnectionError:
            self.rpc              = None
            self.wallet_connected = False
            self.accounts_loaded  = False
        else:
            self.wallet_connected = True

            if not self.accounts_loaded:
                # Update the accounts combo with all the wallets accounts
                self._update_accounts()
                self._update_accounts_combo()
                self.accounts_loaded = True

        self.connected_lbl_dyn.setText('Yes' if self.wallet_connected else 'No')
        self.unlocked_lbl_dyn.setText('No' if self.wallet_locked else 'Yes')

    def create_accounts_box(self):
        accounts_groupbox = QGroupBox()
        accounts_layout   = QVBoxLayout()

        source_lbl = QLabel('Source:')
        # Set to default account or a list selector
        self.source_combo = QComboBox()
        # The other accounts will be filled when connected to the RPC
        self.source_combo.addItem(self.raiconfig['default_account'])
        accounts_layout.addWidget(source_lbl)
        accounts_layout.addWidget(self.source_combo)

        dest_lbl       = QLabel('Destination:')
        self.dest_edit = QLineEdit('x' * 64)
        self._resize_to_content(self.dest_edit)

        self.dest_edit.setText('')
        self.dest_edit.setPlaceholderText('Destination account')
        accounts_layout.addWidget(dest_lbl)
        accounts_layout.addWidget(self.dest_edit)

        amount_lbl       = QLabel('Amount:')
        amount_hbox      = QHBoxLayout()
        self.amount_edit = QLineEdit('')
        self.amount_edit.setPlaceholderText('Amount to send')

        accounts_layout.addWidget(amount_lbl)
        self.unit_combo = _unit_combo()
        self.unit_combo.setCurrentText(self.config_window.unit_combo.currentText())
        self.unit_combo.currentIndexChanged.connect(self._update_accounts_combo)
        amount_hbox.addWidget(self.amount_edit)
        amount_hbox.addWidget(self.unit_combo)
        accounts_layout.addLayout(amount_hbox)

        incamount_check = QCheckBox('Increase needed amount (helps masking transaction, '
                                    'excess returns to account)')
        self.incamount_edit = QLineEdit('')
        self.incamount_edit.setPlaceholderText('Amount to increase')
        self.incamount_edit.setEnabled(False)
        incamount_check.stateChanged.connect(
                lambda: self.incamount_edit.setEnabled(incamount_check.isChecked())
        )
        accounts_layout.addWidget(incamount_check)
        accounts_layout.addWidget(self.incamount_edit)

        accounts_groupbox.setLayout(accounts_layout)
        self.main_layout.addWidget(accounts_groupbox)

    def create_mix_box(self):
        mix_groupbox = QGroupBox('Mixing')
        mix_layout = QFormLayout()

        mix_numaccounts_lbl       = QLabel('Accounts:')
        self.mix_numaccounts_spin = QSpinBox()
        self.mix_numaccounts_spin.setValue(self.config_window.mix_numaccounts_spin.value())
        self.mix_numaccounts_spin.setMinimum(1)
        mix_layout.addRow(mix_numaccounts_lbl, self.mix_numaccounts_spin)

        mix_numrounds_lbl       = QLabel('Rounds:')
        self.mix_numrounds_spin = QSpinBox()
        self.mix_numrounds_spin.setValue(self.config_window.mix_numrounds_spin.value())
        self.mix_numrounds_spin.setMinimum(1)
        mix_layout.addRow(mix_numrounds_lbl, self.mix_numrounds_spin)

        mix_groupbox.setLayout(mix_layout)
        self.mixwallet_layout.addWidget(mix_groupbox)

    def create_walletstatus_box(self):
        walletstatus_groupbox = QGroupBox('Wallet Status')
        walletstatus_layout = QFormLayout()

        connected_lbl = QLabel('Connected:')
        self.connected_lbl_dyn = QLabel('Checking')
        walletstatus_layout.addRow(connected_lbl, self.connected_lbl_dyn)

        unlocked_lbl = QLabel('Unlocked:')
        self.unlocked_lbl_dyn = QLabel('Checking')
        walletstatus_layout.addRow(unlocked_lbl, self.unlocked_lbl_dyn)

        walletstatus_groupbox.setLayout(walletstatus_layout)
        self.mixwallet_layout.addWidget(walletstatus_groupbox)

    def create_consolidate_box(self):
        consolidate_groupbox = QGroupBox('Cleanup')
        consolidate_vbox = QVBoxLayout()

        consolidate_lbl = QLabel('Use this button to move '
            'all balances to the main account.')
        self.consolidate_btn = QPushButton('Consolidate')
        self.consolidate_btn.clicked.connect(self.start_consolitating)
        self.delete_empty_check = QCheckBox('Also delete empty accounts')

        consolidate_vbox.addWidget(consolidate_lbl)
        consolidate_vbox.addWidget(self.consolidate_btn)
        consolidate_vbox.addWidget(self.delete_empty_check)

        consolidate_groupbox.setLayout(consolidate_vbox)
        self.main_layout.addWidget(consolidate_groupbox)

    def create_buttons_box(self):
        buttons_groupbox = QGroupBox()
        buttons_layout   = QHBoxLayout()

        self.mix_btn = QPushButton('Mix!')
        self.mix_btn.clicked.connect(self._check_mixable)
        self.settings_btn = QPushButton('Settings')

        def _show_config():
            self.config_window.show()

        self.settings_btn.clicked.connect(_show_config)
        buttons_layout.addWidget(self.mix_btn)
        buttons_layout.addWidget(self.settings_btn)

        buttons_groupbox.setLayout(buttons_layout)
        self.main_layout.addWidget(buttons_groupbox)

    def create_log_box(self):
        self.log_groupbox = QGroupBox('Output')
        log_layout        = QVBoxLayout()
        self.log_text     = QTextBrowser()

        log_layout.addWidget(self.log_text)
        self.log_groupbox.setLayout(log_layout)
        self.main_layout.addWidget(self.log_groupbox)
        self.log_groupbox.setHidden(True)

    def _resize_to_content(self, line_edit):
        text       = line_edit.text()
        font       = QFont('', 0)
        fm         = QFontMetrics(font)
        pixelsWide = fm.width(text)
        pixelsHigh = fm.height()
        line_edit.setFixedSize(pixelsWide, pixelsHigh)

    def _check_mixable(self):
        from raimixer.utils import valid_account

        base_msg = "If this still don't work:\n\n" \
                   "- Check that RaiBlocks 'config.json' file has the options " \
                   "'rpc_enabled' and 'control_enabled' set to \"true\".\n\n" \
                   "- Check the RPC connection settings." \

        if not self.wallet_connected:
            QMessageBox.warning(self, "Wallet closed",
                                "Can't connect to wallet: please open and unlock it. " +
                                base_msg,
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        if self.wallet_locked:
            QMessageBox.warning(self, "Wallet locked",
                                "Wallet is locked; please unlock it",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        if len(self.dest_edit.text()) == 0:
            QMessageBox.warning(self, "Empty destination account",
                                "Empty destination account",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        if not valid_account(self.dest_edit.text()):
            QMessageBox.warning(self, "Invalid destination account",
                                "Invalid destination account",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        amount_txt = self.amount_edit.text()
        if len(amount_txt.strip()) == 0:
            QMessageBox.warning(self, "Empty amount",
                                "Empty amount",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        try:
            float(amount_txt)
        except ValueError:
            QMessageBox.warning(self, "Invalid amount",
                                "Invalid amount",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        incamount_txt = self.incamount_edit.text()
        if len(incamount_txt) > 0:
            try:
                float(incamount_txt)
            except ValueError:
                QMessageBox.warning(self, "Invalid increased amount",
                                    "Invalid increased amount",
                                    QMessageBox.Ok, QMessageBox.Ok)
                return
        else:
            incamount_txt = "0"

        # Check that there is enough balance
        selected_acc     = self._get_selected_account()
        selected_balance = self.accounts[selected_acc][0]
        divider          = self._get_divider()
        needed_balance   = float(amount_txt) + float(incamount_txt)

        if selected_balance < (needed_balance * divider):
            QMessageBox.warning(self, "Balance too low",
                                "Insufficient balance for sending + increase",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        self.start_mixing()

    def _add_text(self, txt):
        self.log_text.append(str(txt))
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)

    def start_mixing(self):
        from raimixer.utils import normalize_amount, NormalizeAmountException

        rai = RaiMixer(self.raiconfig['wallet'], self.mix_numaccounts_spin.value(),
                       self.mix_numrounds_spin.value(), self.rpc)

        divider = self._get_divider()
        try:
            tosend    = normalize_amount(self.amount_edit.text(), divider)
            incamount = self.incamount_edit.text()

            if len(incamount.strip()) == 0:
                incamount = '0'
            initial_tosend = tosend + normalize_amount(incamount, divider)
        except NormalizeAmountException as e:
            QMessageBox.warning(self, "Invalid amount", "Invalid amount",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        self.guimixer = RaiMixerThreadWrapper(rai)
        self.guimixer.set_start_params(
            self._get_selected_account(),
            self.dest_edit.text(),
            tosend,
            initial_tosend,
            self.config_window.mix_sendmultiple_check.isChecked(),
            self.config_window.mix_leaveremainder_check.isChecked(),
            self.raiconfig['representatives']
        )

        self.guimixer.text_available.connect(self._add_text)

        def mix_cancel():
            self.guimixer.terminate()
            self._add_text("\nMixing cancelled by user.")
            QMessageBox.information(self, 'Mixing Cancelled',
                            "Mixing cancelled. Use the 'Consolidate' button in the " +
                            "Settings window to move all the funds to your main account.",
                            QMessageBox.Ok, QMessageBox.Ok)
            restore_gui()

        def restore_gui():
            self.mix_btn.setText('Mix!')
            self.mix_btn.clicked.disconnect(mix_cancel)
            self.mix_btn.clicked.connect(self._check_mixable)
            self._update_accounts()
            self._update_accounts_combo()

        def mix_success():
            QMessageBox.information(self, "Success!",
                             "Mixing successfully completed and sent!",
                             QMessageBox.Ok, QMessageBox.Ok)
            self.accounts_loaded = False
            restore_gui()

        self.guimixer.mixing_finished.connect(mix_success)

        def mix_error(msg):
            QMessageBox.warning(self, "Problem!",
                    f"There was an error while mixing:\n{msg}\n"
                     "Check the text log. You can recover the amounts to the "
                     "main account with the Consolidate button.",
                    QMessageBox.Ok, QMessageBox.Ok)
            self.accounts_loaded = False
            restore_gui()

        self.guimixer.mixing_problem.connect(mix_error)

        self.log_groupbox.setHidden(False)
        self.mix_btn.setText('Cancel')
        self.mix_btn.clicked.disconnect(self._check_mixable)
        self.mix_btn.clicked.connect(mix_cancel)
        self.guimixer.start()

    def start_consolitating(self):
        from raimixer.config import get_raiblocks_config

        raiconfig = get_raiblocks_config()

        self.guicons = RaiCleanThreadWrapper(
            raiconfig["wallet"],
            self._get_selected_account(),
            self.delete_empty_check.isChecked()
        )
        self.guicons.text_available.connect(self._add_text)

        def consolidate_success():
            self._add_text('\nConsolidation completed. Refresh wallet to see the changes.')
            QMessageBox.information(self, "Success!",
                                    "Consolidation successfully completed",
                                    QMessageBox.Ok, QMessageBox.Ok)
            self.mix_btn.setEnabled(True)

        self.guicons.consolidate_finished.connect(consolidate_success)

        def consolidate_error(msg):
            QMessageBox.warning(
                self, "Problem!",
                f"There was an error while consolidating the amounts: {msg} "
                "Check the text log.",
                QMessageBox.Ok, QMessageBox.Ok
            )
            self.mix_btn.setEnabled(True)

        self.log_groupbox.setHidden(False)
        self.mix_btn.setEnabled(False)
        self.guicons.consolidate_problem.connect(consolidate_error)
        self.guicons.start()


class ConfigWindow(QMainWindow):

    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options
        self.initUI()

    def initUI(self):
        central_wid = QWidget(self)
        self.setCentralWidget(central_wid)

        self.main_layout = QVBoxLayout()
        central_wid.setLayout(self.main_layout)

        self.create_connect_box()
        self.create_mixingdefs_box()

        unit_groupbox   = QGroupBox('Default Unit')
        unit_hbox       = QHBoxLayout()
        self.unit_combo = _unit_combo()
        unit_hbox.addWidget(self.unit_combo)
        unit_groupbox.setLayout(unit_hbox)
        self.main_layout.addWidget(unit_groupbox)

        self.create_buttons_box()
        self.setWindowTitle('Settings')

    def reset_values(self):
        raimixer_conf = read_raimixer_config()
        self.addr_edit.setText(raimixer_conf['rpc_address'])
        self.port_edit.setText(raimixer_conf['rpc_port'])
        self.mix_numaccounts_spin.setValue(int(raimixer_conf['num_mixer_accounts']))
        self.mix_sendmultiple_check.setChecked(raimixer_conf['dest_from_multiple'])
        self.mix_numrounds_spin.setValue(int(raimixer_conf['num_mixing_rounds']))

        unit = raimixer_conf['unit'].lower()
        if unit in ('mrai', 'xrb'):
            self.unit_combo.setCurrentText(MRAI_TEXT)
        elif unit == 'krai':
            self.unit_combo.setCurrentText(KRAI_TEXT)
        else:
            raise Exception('Unknown unit in config, use only mrai or krai')

    def create_connect_box(self):
        connect_groupbox = QGroupBox("Node / Wallet's RPC Connection")
        connect_layout   = QVBoxLayout()

        addr_lbl = QLabel('Address:')
        self.addr_edit = QLineEdit(self.options.rpc_address)
        connect_layout.addWidget(addr_lbl)
        connect_layout.addWidget(self.addr_edit)

        port_lbl = QLabel('Port:')
        self.port_edit = QLineEdit(self.options.rpc_port)
        connect_layout.addWidget(port_lbl)
        connect_layout.addWidget(self.port_edit)

        connect_groupbox.setLayout(connect_layout)
        self.main_layout.addWidget(connect_groupbox)

    def create_mixingdefs_box(self):
        mix_groupbox = QGroupBox('Mixing Defaults')
        mix_layout   = QFormLayout()

        mix_numaccounts_lbl       = QLabel('Accounts:')
        self.mix_numaccounts_spin = QSpinBox()
        self.mix_numaccounts_spin.setValue(4)
        mix_layout.addRow(mix_numaccounts_lbl, self.mix_numaccounts_spin)

        self.mix_sendmultiple_check = QCheckBox('Send to the final destination from several '
                                                'mixing accounts')
        self.mix_sendmultiple_check.setChecked(self.options.dest_from_multiple)
        mix_layout.addRow(self.mix_sendmultiple_check)

        self.mix_leaveremainder_check = QCheckBox('Leave the remainder balance in the '
                                                  'mixing accounts')
        self.mix_leaveremainder_check.setChecked(self.options.leave_remainder)
        mix_layout.addRow(self.mix_leaveremainder_check)

        mix_numrounds_lbl       = QLabel('Rounds:')
        self.mix_numrounds_spin = QSpinBox()
        self.mix_numrounds_spin.setValue(2)
        mix_layout.addRow(mix_numrounds_lbl, self.mix_numrounds_spin)

        mix_groupbox.setLayout(mix_layout)
        self.main_layout.addWidget(mix_groupbox)

    def create_buttons_box(self):
        buttons_groupbox = QGroupBox()
        buttons_layout   = QHBoxLayout()

        def _apply():
            conf = {
                'rpc_address': self.addr_edit.text(),
                'rpc_port': self.port_edit.text(),
                'num_mixer_accounts': self.mix_numaccounts_spin.cleanText(),
                'dest_from_multiple': self.mix_sendmultiple_check.isChecked(),
                'leave_remainder': self.mix_leaveremainder_check.isChecked(),
                'num_mixing_rounds': self.mix_numrounds_spin.cleanText(),
                'unit': 'mrai' if self.unit_combo.currentText() == MRAI_TEXT else 'krai'
            }
            write_raimixer_config(conf)
            self.hide()

        apply_btn = QPushButton('Apply')
        apply_btn.clicked.connect(_apply)

        def _cancel():
            self.hide()
            self.reset_values()

        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(_cancel)
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)

        buttons_groupbox.setLayout(buttons_layout)
        self.main_layout.addWidget(buttons_groupbox)


class RaiMixerThreadWrapper(QThread):

    text_available  = pyqtSignal(object)
    mixing_finished = pyqtSignal()
    mixing_problem  = pyqtSignal(object)

    def __init__(self, raimixer_object: RaiMixer) -> None:
        QThread.__init__(self)
        self.mixer = raimixer_object
        self.mixer.set_print_func(lambda txt: self.text_available.emit(txt))

    def set_start_params(self,
                         orig_account: str,
                         dest_account: str,
                         real_tosend: int,
                         initial_tosend: int,
                         final_send_from_multiple: bool,
                         leave_remainder: bool,
                         representatives: List[str]) -> None:

        self.orig_account             = orig_account
        self.dest_account             = dest_account
        self.real_tosend              = real_tosend
        self.initial_tosend           = initial_tosend
        self.final_send_from_multiple = final_send_from_multiple
        self.leave_remainder           = leave_remainder
        self.representatives          = representatives

    def run(self):
        try:
            self.mixer.start(self.orig_account,
                             self.dest_account,
                             self.real_tosend,
                             self.initial_tosend,
                             self.final_send_from_multiple,
                             self.leave_remainder,
                             self.representatives)
            self.mixing_finished.emit()
        except Exception as e:
            self.mixing_problem.emit(str(e))


class RaiCleanThreadWrapper(QThread):

    text_available  = pyqtSignal(object)
    consolidate_finished  = pyqtSignal()
    consolidate_problem   = pyqtSignal(object)

    def __init__(self, wallet, account, delete_empty=False) -> None:
        QThread.__init__(self)
        self.wallet       = wallet
        self.account      = account
        self.delete_empty = delete_empty

    def run(self):
        try:
            consolidate(self.wallet, self.account,
                        print_func=lambda txt: self.text_available.emit(txt))

            if self.delete_empty:
                delete_empty_accounts(self.wallet, self.account,
                        print_func=lambda txt: self.text_available.emit(txt))
            self.consolidate_finished.emit()
        except Exception as e:
            self.consolidate_problem.emit(str(e))
