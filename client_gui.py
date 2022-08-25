import sys

from PyQt5.QtCore import QObject

from client_ui import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore
from client import TCPSocketClient


class UI(Ui_MainWindow):

    def __init__(self, application):
        self.app = application

    def setupUi(self, main):
        super(UI, self).setupUi(main)
        self.reg_log_dialog.hide()
        self.search_button.clicked.connect(self.show_dialog)

    def show_dialog(self):
        self.reg_log_dialog.show()


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()


if __name__ == '__main__':

    client = TCPSocketClient(host='localhost', port=7777, buffer=8192, connect=True)

    app = QApplication([])
    window = UI(client)
    ui = Main()
    window.setupUi(ui)
    ui.show()
    sys.exit(app.exec())
