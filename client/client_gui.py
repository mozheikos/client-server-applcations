"""
Module that define clients GUI logic
"""


import datetime
from threading import Thread
from typing import List

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QPushButton, QListWidgetItem

from client.client_core import TCPSocketClient
from client.gui.client_ui import Ui_MainWindow
from common.config import settings
from templates.templates import Request, User


class ClientUI(QMainWindow):
    """Widget class with custom signals definition"""

    user_wrong_creds = QtCore.pyqtSignal(str)
    user_logged_in = QtCore.pyqtSignal()
    user_register_error = QtCore.pyqtSignal(str)
    contacts_received = QtCore.pyqtSignal()
    history_received = QtCore.pyqtSignal()
    connected = QtCore.pyqtSignal()
    close = QtCore.pyqtSignal()
    find_contact = QtCore.pyqtSignal(list)
    add_contact = QtCore.pyqtSignal()
    new_message = QtCore.pyqtSignal(str)
    auth_error = QtCore.pyqtSignal()
    initialized = QtCore.pyqtSignal()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Handle of close event. Emit close signal
        :param a0: QCloseEvent instance
        :return:
        """

        self.close.emit()


class UI(Ui_MainWindow):
    """GUI logic"""

    # Словарь с цветами фона сообщений. Ключ - результат проверки, является ли
    # отправитель сообщения текущим пользователем. Если не является - это
    # входящее сообщение
    colors = {
        True: (255, 192, 203),
        False: (102, 205, 170)
    }

    def __init__(self, client: TCPSocketClient, application: ClientUI):
        """
        Init
        :param client: TCPSocketClient instance
        :param application: ClientUI instance
        """
        self.application = application
        self.client = client
        self.receive = None

    def setupUi(self, _):
        """
        Initialization method
        :param _: unused
        :return:
        """

        super(UI, self).setupUi(self.application)
        self.client.gui = self.application
        self.reg_log_dialog.hide()
        self.search_list.hide()
        self.set_signals()
        self.message_box.hide()
        self.message.hide()
        self.send.hide()

    def set_signals(self):
        """
        Connects different signals with slots
        :return:
        """

        # connection
        self.application.connected.connect(self.client_login_dialog)
        self.application.close.connect(self.client_close_window)

        # login/register
        self.login_btns.clicked.connect(self.client_login)
        self.reg_btns.clicked.connect(self.client_register)
        self.button_connect.clicked.connect(self.client_connect)
        self.application.user_logged_in.connect(self.client_login_ok)
        self.application.user_wrong_creds.connect(self.client_login_wrong)
        self.application.user_register_error.connect(self.client_register_error)
        self.application.auth_error.connect(self.authorization_error)
        self.application.initialized.connect(self.initialize_ok)

        # render messages and contacts
        self.contacts.doubleClicked.connect(self.render_messages)
        self.application.find_contact.connect(self.render_search)
        self.search_button.clicked.connect(self.find_contacts)
        self.search_list.doubleClicked.connect(self.add_contact)
        self.application.add_contact.connect(self.render)
        self.application.new_message.connect(self.new_message)
        self.send.clicked.connect(self.send_message)

    def authorization_error(self):
        """
        Authorization error slot. If called stops receiving requests,
        close all widgets, disconnects socket and activate connect button
        :return:
        """

        self.receive.join(timeout=1)
        self.button_connect.setEnabled(True)
        self.reg_log_dialog.hide()
        self.contacts.clear()
        self.message_box.hide()
        self.send.hide()
        self.message.hide()

    def send_message(self):
        """
        Slot to send outbox message. Get text from input, put it to
        message box and call clients send_message method
        :return:
        """

        text = self.message.text()
        self.message.clear()
        contact = self.contacts.selectedItems()[0].text()
        self.client.message(text, contact)
        text = f"{self.client.user.login} {datetime.datetime.now().strftime(settings.DATE_FORMAT)}\n{text}"
        self.render_message(text, QColor(*self.colors.get(False)))

    def new_message(self, contact: str):
        """
        Rendering of new inbox message. If message senders message box is
        open - render message, else - show notification in the top of window
        :param contact: str
        :return:
        """

        if self.contacts.selectedItems() and contact == self.contacts.selectedItems()[0].text():
            messages = self.client.chat.get(contact)
            while len(messages['new']):
                item = messages['new'].popleft()
                msg = f"{item.data.from_} {item.data.date}\n{item.data.message}"
                color = QColor(*self.colors.get(item.data.from_ == contact))
                self.render_message(msg, color)
                messages['was_read'].append(item)
        else:
            self.notification.setText(f"New message from {contact}")

    def find_contacts(self):
        """
        Slot to handle FIND button click. Get name from input and call
        clients find method
        :return:
        """

        value = self.search_input.text()
        self.client.find_contact(value)

    def add_contact(self):
        """
        Handle add contact to contact list by double-clicking on username
        if found list. Get username and call add_contact client method
        :return:
        """

        contact = self.search_list.selectedItems()[0].text()
        self.search_list.clear()
        self.search_input.clear()
        self.client.add_contact(contact)
        self.search_list.hide()

    def render_search(self, users: List[User]):
        """
        Render search list after signal from client application
        :param users: List[Users]
        :return:
        """

        self.search_list.clear()

        for user in users:
            contact = QListWidgetItem(user.login)
            self.search_list.addItem(contact)
        self.search_list.show()

    def render_message(self, msg: str, color: QColor):
        """
        Render new message to chat
        :param msg: str
        :param color: QColor
        :return:
        """

        mess = QListWidgetItem(msg)
        mess.setBackground(color)
        self.message_box.addItem(mess)

    def render_messages(self):
        """
        Render message box after double-click on contact
        :return:
        """

        self.message_box.show()
        self.message.show()
        self.send.show()

        contact = self.contacts.selectedItems()[0].text()
        messages = self.client.chat.get(contact)
        self.message_box.clear()
        for message in messages['was_read'] + messages['new']:
            message: Request
            mess = f"{message.data.from_} {message.data.date}\n" \
                   f"{message.data.message}"
            color = QColor(*self.colors.get(message.data.from_ == contact))
            self.render_message(mess, color)
        messages['was_read'].extend(messages['new'])
        messages['new'].clear()
        if self.notification.text() and self.notification.text().split()[-1] == contact:
            self.notification.clear()

    def client_close_window(self):
        """
        Normally finishing processes and send message to server when app window closing
        :return:
        """

        if self.client.is_connected:
            self.client.quit()
            self.client.shutdown()
            self.reg_log_dialog.hide()
            self.input_login.setText('')
            self.input_password.setText('')
            self.button_connect.setEnabled(True)
            self.client.is_connected = False
            self.receive.join(timeout=1)
            self.receive = None

    def client_connect(self):
        """
        Start receiving thread and connect server on button click
        :return:
        """

        self.client.connect()
        self.receive = Thread(target=self.client.receive, name='client', daemon=True)
        self.receive.start()

    def client_login_dialog(self):
        """
        Show client login/register dialog after successfully connected
        :return:
        """

        self.button_connect.setDisabled(True)
        self.reg_log_dialog.show()

    def client_register(self, e: QPushButton):
        """
        Handle register dialog. Takes button value, then get value of inputs, compare password and confirm:
        if they are same - send register request, else: show attention
        :param e: QPushButton
        :return:
        """

        if e.text() == '&OK':
            login = self.reg_login_input.text()
            passwd_1 = self.reg_passwd_input.text()
            passwd_2 = self.reg_passwd_input_2.text()

            if passwd_1 == passwd_2:
                self.client.login(login, passwd_1, True)
            else:
                self.reg_error.setText("password and confirm dont match")
        else:
            self.client_close_window()

    def client_register_error(self, text: str):
        """
        Show notification when register failed by server
        :param text: str
        :return:
        """

        self.reg_error.setText(text)

    def client_login_ok(self):
        """
        If login OK - hide login dialog and starts client initializing
        :return:
        """

        self.reg_log_dialog.hide()
        self.client.get_server_data()

    def initialize_ok(self):
        """
        Render interface after finishing initialization
        :return:
        """

        self.username.setText(self.client.user.login)
        self.render()

    def render_contact(self, name: str):
        """
        Render contact to contact list
        :param name: str
        :return:
        """

        contact = QListWidgetItem(name)
        self.contacts.addItem(contact)

    def render(self):
        """
        Rendering contact list
        :return:
        """

        self.contacts.clear()

        for name in self.client.chat.keys():
            self.render_contact(name)

    def client_login_wrong(self, text: str):
        """
        Show notification when login failed
        :param text: str
        :return:
        """

        self.login_wrong.setText(text)

    def client_login(self, e: QPushButton):
        """
        Handle buttons on login dialog. If OK - takes login and password and send login request
        :param e: QPushButton
        :return:
        """

        if e.text() == '&OK':
            login = self.input_login.text()
            passwd = self.input_password.text()
            self.client.login(login, passwd)
        else:
            self.client_close_window()
