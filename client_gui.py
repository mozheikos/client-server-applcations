import sys
from threading import Thread
from time import sleep
from typing import Dict

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QListWidgetItem

from client import TCPSocketClient
from client_ui import Ui_MainWindow
from templates.templates import Request


class ClientUI(QMainWindow):

    user_wrong_creds = QtCore.pyqtSignal(str)
    user_logged_in = QtCore.pyqtSignal()
    user_register_error = QtCore.pyqtSignal(str)
    contacts_received = QtCore.pyqtSignal()
    history_received = QtCore.pyqtSignal()
    connected = QtCore.pyqtSignal()
    close = QtCore.pyqtSignal()

    def __init__(self):
        super(ClientUI, self).__init__()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.close.emit()


class UI(Ui_MainWindow):

    def __init__(self, client: TCPSocketClient, application: ClientUI):
        self.application = application
        self.client = client
        self.receive = Thread(target=client.receive, name='client', daemon=True)

    def setupUi(self, _):
        super(UI, self).setupUi(self.application)
        self.client.gui = self.application
        self.reg_log_dialog.hide()
        self.set_signals()

    def set_signals(self):
        self.application.connected.connect(self.client_login_dialog)
        self.application.close.connect(self.client_close_window)

        self.login_btns.clicked.connect(self.client_login)
        self.reg_btns.clicked.connect(self.client_register)
        self.button_connect.clicked.connect(self.client_connect)
        self.application.user_logged_in.connect(self.client_login_ok)
        self.application.user_wrong_creds.connect(self.client_login_wrong)
        self.application.user_register_error.connect(self.client_register_error)
        self.contacts.doubleClicked.connect(self.render_messages)

    def render_messages(self):

        colors = {
            True: (255, 192, 203),
            False: (102, 205, 170)
        }

        contact = self.contacts.selectedItems()[0]
        messages = self.client.chat.get(contact.text())
        for message in messages['was_read']:
            message: Request
            mess = f"{message.data.from_} {message.data.date}\n" \
                   f"{message.data.message}"
            mess = QListWidgetItem(mess)
            mess.setBackground(QColor(*colors.get(message.data.from_ == contact.text())))
            self.message_box.addItem(mess)

    def client_close_window(self):
        if self.client.is_connected:
            self.client.quit()
            self.client.shutdown()
            self.reg_log_dialog.hide()
            self.input_login.setText('')
            self.input_password.setText('')
            self.button_connect.setEnabled(True)
            self.client.is_connected = False
            self.receive.join(timeout=1)

    def client_connect(self):
        self.client.connect()
        self.receive.start()

    def client_login_dialog(self):
        self.button_connect.setDisabled(True)
        self.reg_log_dialog.show()

    def client_register(self, e: QPushButton):
        if e.text() == '&OK':
            login = self.reg_login_input.text()
            passwd_1 = self.reg_passwd_input.text()
            passwd_2 = self.reg_passwd_input_2.text()

            if passwd_1 == passwd_2:
                self.client.register(login, passwd_1)
            else:
                self.reg_error.setText("password and confirm dont match")

    def client_register_error(self, text: str):
        self.reg_error.setText(text)

    def client_login_ok(self):
        self.reg_log_dialog.hide()
        self.client.get_contacts()
        while not self.client.initialized:
            sleep(0.1)

        self.render()

    def render_contact(self, name: str):
        contact = QListWidgetItem(name)
        self.contacts.addItem(contact)

    def render(self):

        for name in self.client.chat.keys():
            self.render_contact(name)

    def client_login_wrong(self, text: str):
        self.login_wrong.setText(text)

    def client_login(self, e: QPushButton):
        if e.text() == '&OK':
            login = self.input_login.text()
            passwd = self.input_password.text()
            self.client.login(login, passwd)
        else:
            self.client_close_window()


if __name__ == '__main__':

    clt = TCPSocketClient(host='localhost', port=7777, buffer=8192, connect=False)

    app = QApplication([])
    ui = ClientUI()
    window = UI(clt, ui)
    window.setupUi(ui)
    ui.show()
    sys.exit(app.exec())
