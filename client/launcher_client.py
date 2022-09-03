"""
Client launcher
"""


import sys

from PyQt5.QtWidgets import QApplication

from client_core import TCPSocketClient
from client_gui import ClientUI, UI

if __name__ == '__main__':
    clt = TCPSocketClient(host='localhost', port=7777, buffer=8192, connect=False)

    app = QApplication([])
    ui = ClientUI()
    window = UI(clt, ui)
    window.setupUi(ui)
    ui.show()
    sys.exit(app.exec())
