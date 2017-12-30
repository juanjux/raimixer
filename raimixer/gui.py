import sys
from typing import Tuple

from raimixer.rairpc import RaiRPC

from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QApplication,
        QGroupBox, QLabel, QLineEdit, QSpinBox, QComboBox, QTextBrowser,
        QCheckBox, QMainWindow
)
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from requests import ConnectionError

# TODO: store/load config (appdirs.user_config_dir()/raimixer_gui.json)
# TODO: simplify the var names in the private methods
# TODO: connect with raimixer and make it work
# TODO: progress bar
# TODO: tooltips


def _units_combo():
    units_combo = QComboBox()
    units_combo.addItem('XRB/MRAI')
    units_combo.addItem('KRAI')
    return units_combo


class RaimixerGUI(QMainWindow):

    def __init__(self, options, raiconfig, parent=None):
        super().__init__(parent)
        self.options = options
        self.raiconfig = raiconfig
        self.initUI()
        self.wallet_connected = False
        self.wallet_locked = True
        self.config_window = ConfigWindow(options, raiconfig, self)

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

        self.create_buttons_box()
        self.create_log_box()

        self.setWindowTitle('RaiMixer')

        # Timer to check & update the connection status to the wallet
        self.wallet_conn_timer = QTimer(self)
        self.wallet_conn_timer.timeout.connect(self.update_wallet_conn)
        self.wallet_conn_timer.start(1000)

    def update_wallet_conn(self):
        rpc = RaiRPC(self.source_combo.currentText, self.raiconfig['wallet'],
                     self.options.rpc_address, self.options.rpc_port)

        try:
            self.wallet_locked = rpc.wallet_locked()
        except ConnectionError:
            self.wallet_connected = False
        else:
            self.wallet_connected = True

        self.connected_lbl_dyn.setText('Yes' if self.wallet_connected else 'No')
        self.unlocked_lbl_dyn.setText('No' if self.wallet_locked else 'Yes')

    def create_accounts_box(self):
        accounts_groupbox = QGroupBox()
        accounts_layout = QVBoxLayout()

        source_lbl = QLabel('Source:')
        # Set to default account or a list selector
        self.source_combo = QComboBox()
        # XXX RPC call to read all wallet accounts and load them here
        self.source_combo.addItem(self.raiconfig['default_account'])
        accounts_layout.addWidget(source_lbl)
        accounts_layout.addWidget(self.source_combo)

        dest_lbl = QLabel('Destination:')
        dest_edit = QLineEdit('x' * 64)
        self._resize_to_content(dest_edit)

        dest_edit.setText('')
        dest_edit.setPlaceholderText('Destination account')
        accounts_layout.addWidget(dest_lbl)
        accounts_layout.addWidget(dest_edit)

        amount_lbl = QLabel('Amount:')
        amount_hbox = QHBoxLayout()
        amount_edit = QLineEdit('')
        amount_edit.setPlaceholderText('Amount to send')
        accounts_layout.addWidget(amount_lbl)
        units_combo = _units_combo()
        amount_hbox.addWidget(amount_edit)
        amount_hbox.addWidget(units_combo)
        accounts_layout.addLayout(amount_hbox)

        incamount_check = QCheckBox('Increase needed amount (helps masking transaction, '
                                    'excess returns to account)')
        incamount_edit = QLineEdit('')
        incamount_edit.setPlaceholderText('Amount to increase')
        incamount_edit.setEnabled(False)
        incamount_check.stateChanged.connect(
                lambda: incamount_edit.setEnabled(incamount_check.isChecked())
        )
        accounts_layout.addWidget(incamount_check)
        accounts_layout.addWidget(incamount_edit)

        accounts_groupbox.setLayout(accounts_layout)
        self.main_layout.addWidget(accounts_groupbox)

    def create_mix_box(self):
        mix_groupbox = QGroupBox('Mixing')
        mix_layout = QFormLayout()

        mix_numaccounts_lbl = QLabel('Accounts:')
        mix_numaccounts_spin = QSpinBox()
        # XXX set default from settings
        mix_numaccounts_spin.setValue(4)
        mix_layout.addRow(mix_numaccounts_lbl, mix_numaccounts_spin)

        mix_numrounds_lbl = QLabel('Rounds:')
        mix_numrounds_spin = QSpinBox()
        mix_numrounds_spin.setValue(2)
        mix_layout.addRow(mix_numrounds_lbl, mix_numrounds_spin)

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

    def create_buttons_box(self):
        buttons_groupbox = QGroupBox()
        buttons_layout = QHBoxLayout()

        mix_btn = QPushButton('Mix!')
        settings_btn = QPushButton('Settings')

        def _show_config():
            self.config_window.show()

        settings_btn.clicked.connect(_show_config)
        buttons_layout.addWidget(mix_btn)
        buttons_layout.addWidget(settings_btn)

        buttons_groupbox.setLayout(buttons_layout)
        self.main_layout.addWidget(buttons_groupbox)

    def create_log_box(self):
        self.log_groupbox = QGroupBox('Output')
        log_layout = QVBoxLayout()

        log_text = QTextBrowser()
        log_layout.addWidget(log_text)
        self.log_groupbox.setLayout(log_layout)
        self.main_layout.addWidget(self.log_groupbox)
        self.log_groupbox.setHidden(True)

    def _resize_to_content(self, line_edit):
        text = line_edit.text()
        font = QFont('', 0)
        fm = QFontMetrics(font)
        pixelsWide = fm.width(text)
        pixelsHigh = fm.height()
        line_edit.setFixedSize(pixelsWide, pixelsHigh)


class ConfigWindow(QMainWindow):

    def __init__(self, options, raiconfig, parent=None):
        super().__init__(parent)
        self.options = options
        self.raiconfig = raiconfig
        self.initUI()

    def initUI(self):
        central_wid = QWidget(self)
        self.setCentralWidget(central_wid)

        self.main_layout = QVBoxLayout()
        central_wid.setLayout(self.main_layout)

        self.create_connect_box()
        self.create_mixingdefs_box()

        unit_groupbox = QGroupBox('Default Unit')
        unit_hbox = QHBoxLayout()
        unit_combo = _units_combo()
        unit_hbox.addWidget(unit_combo)
        unit_groupbox.setLayout(unit_hbox)
        self.main_layout.addWidget(unit_groupbox)

        self.create_buttons_box()
        self.setWindowTitle('Settings')

    def create_connect_box(self):
        connect_groupbox = QGroupBox("Node / Wallet's RPC Connection")
        connect_layout = QVBoxLayout()

        addr_lbl = QLabel('Address:')
        # XXX read from settings json, default to raiblocks config
        addr_edit = QLineEdit(self.options.rpc_address)
        connect_layout.addWidget(addr_lbl)
        connect_layout.addWidget(addr_edit)

        port_lbl = QLabel('Port:')
        # XXX ditto
        port_edit = QLineEdit(self.options.rpc_port)
        connect_layout.addWidget(port_lbl)
        connect_layout.addWidget(port_edit)

        connect_groupbox.setLayout(connect_layout)
        self.main_layout.addWidget(connect_groupbox)

    def create_mixingdefs_box(self):
        mix_groupbox = QGroupBox('Mixing Defaults')
        mix_layout = QFormLayout()

        mix_numaccounts_lbl = QLabel('Accounts:')
        mix_numaccounts_spin = QSpinBox()
        # XXX set default from loaded settings
        mix_numaccounts_spin.setValue(4)
        mix_layout.addRow(mix_numaccounts_lbl, mix_numaccounts_spin)

        mix_numrounds_lbl = QLabel('Rounds:')
        mix_numrounds_spin = QSpinBox()
        mix_numrounds_spin.setValue(2)
        mix_layout.addRow(mix_numrounds_lbl, mix_numrounds_spin)

        mix_groupbox.setLayout(mix_layout)
        self.main_layout.addWidget(mix_groupbox)

    def create_buttons_box(self):
        buttons_groupbox = QGroupBox()
        buttons_layout = QHBoxLayout()

        apply_btn = QPushButton('Apply')
        cancel_btn = QPushButton('Cancel')
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)

        buttons_groupbox.setLayout(buttons_layout)
        self.main_layout.addWidget(buttons_groupbox)
