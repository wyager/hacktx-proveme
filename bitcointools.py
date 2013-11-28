#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2011 thomasv@gitorious
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import re
import pkgutil
import sys, os, time, json
import optparse
import platform
from decimal import Decimal
import traceback
import hashlib

try:
    import ecdsa  
except ImportError:
    sys.exit("Error: python-ecdsa does not seem to be installed. Try 'sudo pip install ecdsa'")

try:
    import aes
except ImportError:
    sys.exit("Error: AES does not seem to be installed. Try 'sudo pip install slowaes'")


is_local = os.path.dirname(os.path.realpath(__file__)) == os.getcwd()

import __builtin__
__builtin__.use_local_modules = is_local or is_android

# load local module as electrum
if __builtin__.use_local_modules:
    import imp
    imp.load_module('electrum', *imp.find_module('lib'))
    imp.load_module('electrum_gui', *imp.find_module('gui'))

from electrum import *


class BitcoinManager():
    def __init__(self):
        config_options = {'show_labels': False, 'tx_fee': .0002, 'verbose': False, 'language': None, 'from_addr': None, 'electrum_path': None, 'gui': None, 'show_all': False, 'wallet_path': None, 'change_addr': None, 'server': None, 'bitkey': None, 'proxy': None, 'oneserver': False, 'concealed': False, 'gap_limit': None, 'offline': False, 'password': None, 'portable': False}
        #config_options['electrum_path'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'electrum_data')

        for k, v in config_options.items():
            if v is None: config_options.pop(k)

        set_verbosity(config_options.get('verbose'))
        print config_options
        config = SimpleConfig(config_options)

        # instanciate wallet for command-line
        storage = WalletStorage(config)
        wallet = Wallet(storage)


        # elif cmd.name in ['payto', 'mktx']:
        #     domain = [options.from_addr] if options.from_addr else None
        #     args = [ 'mktx', args[1], Decimal(args[2]), Decimal(options.tx_fee) if options.tx_fee else None, options.change_addr, domain ]
            
        network = Network(config)
        if not network.start(wait=True):
            print_msg("Not connected, aborting.")
            sys.exit(1)
        time.sleep(2)
        print_error("Connected to " + network.interface.connection_msg)
        if wallet:
            wallet.start_threads(network)
            wallet.update()
        self.network = network
        self.wallet = wallet

    def __del__(self):
        if self.network:
            if self.wallet:
                self.wallet.stop_threads()
            self.network.stop()
            time.sleep(.1)

    def send_money(self, to_address, amount, fee = None, change_addr = None):
        try:
            cmd_runner = Commands(self.wallet, self.network)
            result = cmd_runner.payto(to_address, amount, fee, change_addr)
        except Exception as e:
            print_error("Error sending money.")
            import traceback
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        return result

    def get_balance(self):
        try:
            cmd_runner = Commands(self.wallet, self.network)
            result = cmd_runner.getbalance()
        except Exception as e:
            print_error("Error getting balance.")
            import traceback
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        return result

    def get_addresses(self):
        return self.wallet.addresses()

    def get_address_history(self, address):
        return self.network.synchronous_get([ ('blockchain.address.get_history',[address]) ])[0]

    def get_raw_transaction(self, txid, height=0):
        try:
            cmd_runner = Commands(self.wallet, self.network)
            result = cmd_runner.getrawtransaction(txid, height)
        except Exception as e:
            print_error("Error getting raw transaction.")
            import traceback
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        return result

    def get_block_timestamp(self, height):
        return self.network.blockchain.read_header(height)['timestamp']

def makeAddressFromData(data):
    pubkey = hashlib.sha256(data).digest()
    return bitcoin.public_key_to_bc_address(pubkey)

if __name__ == '__main__':
    bitcoin_manager = BitcoinManager()
    print bitcoin_manager.get_balance()
    #print bitcoin_manager.send_money("18281kf9yRJehUEKPftjhz16N3nAv6fBnt", Decimal(".0003"))
    print "The FBI has " + str(bitcoin_manager.get_address_history("1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX"))
    custom_addr = makeAddressFromData("Testing some stuff")
    print "Our custom address has done " + str(bitcoin_manager.get_address_history(custom_addr))