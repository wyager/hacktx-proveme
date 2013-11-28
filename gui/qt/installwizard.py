from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.QtCore as QtCore

from electrum.i18n import _
from electrum import Wallet, mnemonic

from seed_dialog import SeedDialog
from network_dialog import NetworkDialog
from util import *
from amountedit import AmountEdit

import sys
import threading

class InstallWizard(QDialog):

    def __init__(self, config, network, storage):
        QDialog.__init__(self)
        self.config = config
        self.network = network
        self.storage = storage
        self.setMinimumSize(575, 400)
        self.setWindowTitle('Electrum')
        self.connect(self, QtCore.SIGNAL('accept'), self.accept)

        self.stack = QStackedLayout()
        self.setLayout(self.stack)


    def set_layout(self, layout):
        w = QWidget()
        w.setLayout(layout)
        self.stack.setCurrentIndex(self.stack.addWidget(w))


    def restore_or_create(self):

        grid = QGridLayout()
        grid.setSpacing(5)

        msg = _("Electrum could not find an existing wallet.")+"\n\n"+_("Did you use Electrum before and want to restore a previous wallet or is this your first time and do you want to create a new wallet?")+"\n"
        label = QLabel(msg)
        label.setWordWrap(True)
        grid.addWidget(label, 0, 0)

        gb = QGroupBox()

        b1 = QRadioButton(gb)
        b1.setText(_("Create new wallet"))
        b1.setChecked(True)

        b2 = QRadioButton(gb)
        b2.setText(_("Restore wallet from seed"))

        b3 = QRadioButton(gb)
        b3.setText(_("Restore wallet from master public key"))

        grid.addWidget(b1,1,0)
        grid.addWidget(b2,2,0)
        grid.addWidget(b3,3,0)

        vbox = QVBoxLayout()
        self.set_layout(vbox)

        vbox.addLayout(grid)
        vbox.addStretch(1)
        vbox.addLayout(ok_cancel_buttons(self, _('Next')))

        if not self.exec_():
            return
        
        if b1.isChecked():
            answer = 'create'
        elif b2.isChecked():
            answer = 'restore'
        else:
            answer = 'watching'

        return answer


    def verify_seed(self, wallet):
        r = self.seed_dialog(False)
        if not r:
            return

        if r != wallet.get_mnemonic(None):
            QMessageBox.warning(None, _('Error'), _('Incorrect seed'), _('OK'))
            return False
        else:
            return True


    def seed_dialog(self, is_restore=True):

        vbox = QVBoxLayout()
        if is_restore:
            msg = _("Please enter your wallet seed.") + "\n"
        else:
            msg = _("Your seed is important!") \
                + "\n" + _("To make sure that you have properly saved your seed, please retype it here.")
        
        logo = QLabel()
        logo.setPixmap(QPixmap(":icons/seed.png").scaledToWidth(56))
        logo.setMaximumWidth(60)

        label = QLabel(msg)
        label.setWordWrap(True)

        seed_e = QTextEdit()
        seed_e.setMaximumHeight(100)

        vbox.addWidget(label)

        grid = QGridLayout()
        grid.addWidget(logo, 0, 0)
        grid.addWidget(seed_e, 0, 1)

        vbox.addLayout(grid)

        vbox.addStretch(1)
        vbox.addLayout(ok_cancel_buttons(self, _('Next')))

        self.set_layout(vbox)
        if not self.exec_():
            return

        seed = unicode(seed_e.toPlainText())

        if not seed:
            QMessageBox.warning(None, _('Error'), _('No seed'), _('OK'))
            return

        return seed



    def waiting_dialog(self, task, msg= _("Electrum is generating your addresses, please wait.")):
        def target():
            task()
            self.emit(QtCore.SIGNAL('accept'))

        vbox = QVBoxLayout()
        self.waiting_label = QLabel(msg)
        vbox.addWidget(self.waiting_label)
        self.set_layout(vbox)
        t = threading.Thread(target = target)
        t.start()
        self.exec_()



    def mpk_dialog(self):

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(_("Please enter your master public key.")))

        grid = QGridLayout()
        grid.setSpacing(8)

        label = QLabel(_("Key")) 
        grid.addWidget(label, 0, 0)
        mpk_e = QTextEdit()
        mpk_e.setMaximumHeight(100)
        grid.addWidget(mpk_e, 0, 1)

        label = QLabel(_("Chain")) 
        #grid.addWidget(label, 1, 0)
        chain_e = QTextEdit()
        chain_e.setMaximumHeight(100)
        #grid.addWidget(chain_e, 1, 1)

        vbox.addLayout(grid)

        vbox.addStretch(1)
        vbox.addLayout(ok_cancel_buttons(self, _('Next')))

        self.set_layout(vbox)
        if not self.exec_(): return None, None

        mpk = str(mpk_e.toPlainText()).strip()
        chain = str(chain_e.toPlainText()).strip()
        return mpk, chain


    def network_dialog(self):
        
        grid = QGridLayout()
        grid.setSpacing(5)

        label = QLabel(_("Electrum communicates with remote servers to get information about your transactions and addresses. The servers all fulfil the same purpose only differing in hardware. In most cases you simply want to let Electrum pick one at random if you have a preference though feel free to select a server manually.") + "\n\n" \
                      + _("How do you want to connect to a server:")+" ")
        label.setWordWrap(True)
        grid.addWidget(label, 0, 0)

        gb = QGroupBox()

        b1 = QRadioButton(gb)
        b1.setText(_("Auto connect"))
        b1.setChecked(True)

        b2 = QRadioButton(gb)
        b2.setText(_("Select server manually"))

        #b3 = QRadioButton(gb)
        #b3.setText(_("Stay offline"))

        grid.addWidget(b1,1,0)
        grid.addWidget(b2,2,0)
        #grid.addWidget(b3,3,0)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)

        vbox.addStretch(1)
        vbox.addLayout(ok_cancel_buttons(self, _('Next')))

        self.set_layout(vbox)
        if not self.exec_():
            return
        
        if b2.isChecked():
            return NetworkDialog(self.network, self.config, None).do_exec()

        elif b1.isChecked():
            self.config.set_key('auto_cycle', True, True)
            return

        else:
            self.config.set_key("server", None, True)
            self.config.set_key('auto_cycle', False, True)
            return
        


    def show_seed(self, wallet):
        from seed_dialog import make_seed_dialog
        vbox = make_seed_dialog(wallet.get_mnemonic(None), wallet.imported_keys)
        vbox.addLayout(ok_cancel_buttons(self, _("Next")))
        self.set_layout(vbox)
        return self.exec_()


    def password_dialog(self, wallet):
        msg = _("Please choose a password to encrypt your wallet keys.")+'\n'\
              +_("Leave these fields empty if you want to disable encryption.")
        from password_dialog import make_password_dialog, run_password_dialog
        self.set_layout( make_password_dialog(self, wallet, msg) )

        run_password_dialog(self, wallet, self)


    def run(self):

        action = self.restore_or_create()
        if not action: 
            return

        wallet = Wallet(self.storage)
        gap = self.config.get('gap_limit', 5)
        if gap != 5:
            wallet.gap_limit = gap
            wallet.storage.put('gap_limit', gap, True)

        if action == 'create':
            wallet.init_seed(None)
            if not self.show_seed(wallet):
                return
            if not self.verify_seed(wallet):
                return
            def create():
                wallet.save_seed()
                wallet.synchronize()  # generate first addresses offline
            self.waiting_dialog(create)

        elif action == 'restore':
            # ask for seed and gap.
            seed = self.seed_dialog()
            if not seed:
                return
            try:
                wallet.init_seed(seed)
            except Exception:
                import traceback
                traceback.print_exc(file=sys.stdout)
                QMessageBox.warning(None, _('Error'), _('Incorrect seed'), _('OK'))
                return

            wallet.save_seed()

        elif action == 'watching':
            # ask for seed and gap.
            mpk = self.mpk_dialog()
            if not mpk:
                return
            wallet.seed = ''
            wallet.create_watching_only_wallet(mpk)

        else: raise
                
        #if not self.config.get('server'):
        if self.network:
            self.network_dialog()

        # start wallet threads
        wallet.start_threads(self.network)

        if action == 'restore':

            self.waiting_dialog(lambda: wallet.restore(self.waiting_label.setText))

            if self.network:
                if wallet.is_found():
                    QMessageBox.information(None, _('Information'), _("Recovery successful"), _('OK'))
                else:
                    QMessageBox.information(None, _('Information'), _("No transactions found for this seed"), _('OK'))
            else:
                QMessageBox.information(None, _('Information'), _("This wallet was restored offline. It may contain more addresses than displayed."), _('OK'))

        self.password_dialog(wallet)

        return wallet
