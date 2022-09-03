"""
Server launcher
"""


import sys

from PyQt5.QtWidgets import QApplication

from common.config import settings
from server.server_core import TCPSocketServer, RequestHandler
from server.server_gui import ServerUI, UI

if __name__ == '__main__':
    srv = TCPSocketServer(
        handler=RequestHandler,
        host=settings.HOST,
        port=settings.PORT,
        bind_and_listen=True
    )
    app = QApplication([])
    ui = ServerUI()
    admin = UI(srv, ui)

    admin.setupUi(ui)
    ui.show()
    sys.exit(app.exec())
