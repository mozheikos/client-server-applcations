"""
Module of server GUI
"""


import json
from pathlib import Path
from threading import Thread
from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QPushButton, QListWidgetItem

from common.config import settings
from server.gui.server_ui import Ui_MainWindow
from server.server_core import TCPSocketServer


class ServerUI(QMainWindow):
    """Server GUI application"""

    user_connected = QtCore.pyqtSignal(dict)
    user_disconnected = QtCore.pyqtSignal(tuple)
    console_log = QtCore.pyqtSignal(str)

    def __init__(self):
        super(ServerUI, self).__init__()


class UI(Ui_MainWindow):
    """
    Main server GUI class
    """
    def __init__(self, server: TCPSocketServer, application: ServerUI):
        """
        Init
        :param server: TCPSocketServer
        :param application: ServerUI
        """
        self.application = application
        self.server = server
        self.thread = Thread(target=self.server.serve, name='server', daemon=True)

    def setupUi(self, _):
        """
        Initialization of UI application
        :param _: unused
        :return:
        """
        super(UI, self).setupUi(self.application)
        self.get_server_settings()
        self.host_port_dialog.hide()
        self.restart_needed.hide()
        self.server.gui = self.application
        self.set_signals()
        self.thread.start()

    def set_signals(self):
        """
        Initialize signal handlers
        :return:
        """
        self.application.user_connected.connect(self.connected_add_row)
        self.application.user_disconnected.connect(self.connected_delete_row)
        self.application.console_log.connect(self.console_logging)
        self.admin_edit_conn.clicked.connect(self.edit_connect)
        self.confirm_btns.clicked.connect(self.confirm_settings)

    def console_logging(self, text: str):
        """
        Send message ti server console
        :param text: str
        :return:
        """
        self.console_log.addItem(QListWidgetItem(text))

    def confirm_settings(self, e: QPushButton):
        """
        Handler of confirm button in server settings. Saves new values to config.json.
        Shows attention of restart needed
        :param e: QPushButton
        :return:
        """
        if e.text() == '&OK':

            path = Path(__file__).resolve().parent.parent

            host = self.settings_host.text()
            port = self.settings_port.text()
            database = self.settings_db_choice.currentText()

            with open(f'{path}/common/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                if host:
                    config['HOST'] = host
                if port:
                    config['PORT'] = int(port)

                config['DATABASE'] = database

            with open(f'{path}/common/config.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(config, indent=4, ensure_ascii=False))
            self.restart_needed.show()
        self.host_port_dialog.hide()

    def edit_connect(self):
        """
        Show dialog of changing server settings
        :return:
        """
        self.host_port_dialog.raise_()
        self.host_port_dialog.show()

    def connected_add_row(self, row: Dict[str, str]):
        """
        Add client data to connected clients table
        :param row: Dict[str, str]
        :return:
        """

        count = self.admin_clients.rowCount()
        self.admin_clients.setRowCount(count + 1)
        self.admin_clients.setItem(count, 0, QTableWidgetItem(row['ip']))
        self.admin_clients.setItem(count, 1, QTableWidgetItem(row['port']))
        self.admin_clients.setItem(count, 2, QTableWidgetItem(row['date']))
        self.admin_clients.resizeColumnsToContents()

    def connected_delete_row(self, addr: tuple):
        """
        Delete row in connected clients table when client disconnected
        :param addr: Tuple[str, str]
        :return:
        """

        for i in range(self.admin_clients.rowCount()):
            if self.admin_clients.item(i, 0).text() == addr[0] and self.admin_clients.item(i, 1).text() == addr[1]:
                self.admin_clients.removeRow(i)
                break

    def get_server_settings(self):
        """
        Set server settings from json-file
        :return:
        """

        path = Path(__file__).resolve().parent.parent
        with open(f"{path}/db/config.json", 'r', encoding='utf-8') as f:
            databases = json.load(f)

        self.settings_db_choice.addItems(list(databases['ServerDatabase'].keys()))
        self.admin_host.setText(settings.HOST)
        self.admin_port.setText(str(settings.PORT))
        self.admin_database.setText(settings.DATABASE)
