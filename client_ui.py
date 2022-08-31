# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'client.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(802, 607)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.search_input = QtWidgets.QLineEdit(self.centralwidget)
        self.search_input.setGeometry(QtCore.QRect(0, 40, 191, 25))
        self.search_input.setObjectName("search_input")
        self.search_button = QtWidgets.QPushButton(self.centralwidget)
        self.search_button.setGeometry(QtCore.QRect(190, 40, 66, 25))
        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")
        font.setPointSize(13)
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(50)
        self.search_button.setFont(font)
        self.search_button.setObjectName("search_button")
        self.contacts = QtWidgets.QListWidget(self.centralwidget)
        self.contacts.setGeometry(QtCore.QRect(0, 70, 256, 511))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.contacts.sizePolicy().hasHeightForWidth())
        self.contacts.setSizePolicy(sizePolicy)
        self.contacts.setSizeIncrement(QtCore.QSize(1, 1))
        self.contacts.setBaseSize(QtCore.QSize(1, 1))
        self.contacts.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.contacts.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.contacts.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.contacts.setEditTriggers(QtWidgets.QAbstractItemView.EditKeyPressed)
        self.contacts.setProperty("showDropIndicator", False)
        self.contacts.setAlternatingRowColors(True)
        self.contacts.setObjectName("contacts")
        self.reg_log_dialog = QtWidgets.QTabWidget(self.centralwidget)
        self.reg_log_dialog.setEnabled(True)
        self.reg_log_dialog.setGeometry(QtCore.QRect(220, 140, 401, 371))
        self.reg_log_dialog.setAutoFillBackground(False)
        self.reg_log_dialog.setTabPosition(QtWidgets.QTabWidget.North)
        self.reg_log_dialog.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.reg_log_dialog.setElideMode(QtCore.Qt.ElideNone)
        self.reg_log_dialog.setTabBarAutoHide(False)
        self.reg_log_dialog.setObjectName("reg_log_dialog")
        self.login_dialog = QtWidgets.QWidget()
        self.login_dialog.setAutoFillBackground(False)
        self.login_dialog.setObjectName("login_dialog")
        self.login_btns = QtWidgets.QDialogButtonBox(self.login_dialog)
        self.login_btns.setGeometry(QtCore.QRect(80, 200, 241, 81))
        self.login_btns.setOrientation(QtCore.Qt.Vertical)
        self.login_btns.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.login_btns.setCenterButtons(True)
        self.login_btns.setObjectName("login_btns")
        self.input_login = QtWidgets.QLineEdit(self.login_dialog)
        self.input_login.setGeometry(QtCore.QRect(80, 50, 241, 30))
        self.input_login.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.input_login.setClearButtonEnabled(True)
        self.input_login.setObjectName("input_login")
        self.input_password = QtWidgets.QLineEdit(self.login_dialog)
        self.input_password.setGeometry(QtCore.QRect(80, 120, 241, 30))
        self.input_password.setStyleSheet("type=\"password\"")
        self.input_password.setText("")
        self.input_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_password.setClearButtonEnabled(True)
        self.input_password.setObjectName("input_password")
        self.label_login = QtWidgets.QLabel(self.login_dialog)
        self.label_login.setGeometry(QtCore.QRect(80, 20, 241, 20))
        self.label_login.setObjectName("label_login")
        self.label_password = QtWidgets.QLabel(self.login_dialog)
        self.label_password.setGeometry(QtCore.QRect(80, 90, 241, 20))
        self.label_password.setObjectName("label_password")
        self.login_wrong = QtWidgets.QLabel(self.login_dialog)
        self.login_wrong.setGeometry(QtCore.QRect(25, 165, 350, 30))
        self.login_wrong.setStyleSheet("color: rgb(239, 41, 41);")
        self.login_wrong.setText("")
        self.login_wrong.setAlignment(QtCore.Qt.AlignCenter)
        self.login_wrong.setObjectName("login_wrong")
        self.reg_log_dialog.addTab(self.login_dialog, "")
        self.reg_dialog = QtWidgets.QWidget()
        self.reg_dialog.setAutoFillBackground(False)
        self.reg_dialog.setStyleSheet("background-color: rgb(243, 243, 243);")
        self.reg_dialog.setObjectName("reg_dialog")
        self.reg_label_login = QtWidgets.QLabel(self.reg_dialog)
        self.reg_label_login.setGeometry(QtCore.QRect(80, 20, 241, 20))
        self.reg_label_login.setObjectName("reg_label_login")
        self.reg_login_input = QtWidgets.QLineEdit(self.reg_dialog)
        self.reg_login_input.setGeometry(QtCore.QRect(80, 50, 241, 30))
        self.reg_login_input.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.reg_login_input.setClearButtonEnabled(True)
        self.reg_login_input.setObjectName("reg_login_input")
        self.reg_label_passwd = QtWidgets.QLabel(self.reg_dialog)
        self.reg_label_passwd.setGeometry(QtCore.QRect(80, 90, 241, 20))
        self.reg_label_passwd.setObjectName("reg_label_passwd")
        self.reg_passwd_input = QtWidgets.QLineEdit(self.reg_dialog)
        self.reg_passwd_input.setGeometry(QtCore.QRect(80, 120, 241, 30))
        self.reg_passwd_input.setStyleSheet("type=\"password\"")
        self.reg_passwd_input.setText("")
        self.reg_passwd_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.reg_passwd_input.setClearButtonEnabled(True)
        self.reg_passwd_input.setObjectName("reg_passwd_input")
        self.reg_btns = QtWidgets.QDialogButtonBox(self.reg_dialog)
        self.reg_btns.setGeometry(QtCore.QRect(80, 250, 241, 81))
        self.reg_btns.setOrientation(QtCore.Qt.Vertical)
        self.reg_btns.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.reg_btns.setCenterButtons(True)
        self.reg_btns.setObjectName("reg_btns")
        self.reg_passwd_input_2 = QtWidgets.QLineEdit(self.reg_dialog)
        self.reg_passwd_input_2.setGeometry(QtCore.QRect(80, 190, 241, 30))
        self.reg_passwd_input_2.setStyleSheet("type=\"password\"")
        self.reg_passwd_input_2.setText("")
        self.reg_passwd_input_2.setEchoMode(QtWidgets.QLineEdit.Password)
        self.reg_passwd_input_2.setClearButtonEnabled(True)
        self.reg_passwd_input_2.setObjectName("reg_passwd_input_2")
        self.reg_label_passwd_2 = QtWidgets.QLabel(self.reg_dialog)
        self.reg_label_passwd_2.setGeometry(QtCore.QRect(80, 160, 111, 20))
        self.reg_label_passwd_2.setObjectName("reg_label_passwd_2")
        self.reg_error = QtWidgets.QLabel(self.reg_dialog)
        self.reg_error.setGeometry(QtCore.QRect(80, 230, 241, 20))
        self.reg_error.setStyleSheet("color: rgb(239, 41, 41);")
        self.reg_error.setText("")
        self.reg_error.setAlignment(QtCore.Qt.AlignCenter)
        self.reg_error.setObjectName("reg_error")
        self.reg_log_dialog.addTab(self.reg_dialog, "")
        self.send = QtWidgets.QPushButton(self.centralwidget)
        self.send.setGeometry(QtCore.QRect(730, 550, 71, 31))
        self.send.setObjectName("send")
        self.button_connect = QtWidgets.QPushButton(self.centralwidget)
        self.button_connect.setGeometry(QtCore.QRect(0, 5, 89, 30))
        self.button_connect.setObjectName("button_connect")
        self.message_box = QtWidgets.QListWidget(self.centralwidget)
        self.message_box.setGeometry(QtCore.QRect(260, 40, 541, 511))
        self.message_box.setObjectName("message_box")
        self.search_list = QtWidgets.QListWidget(self.centralwidget)
        self.search_list.setGeometry(QtCore.QRect(0, 70, 191, 21))
        self.search_list.setObjectName("search_list")
        self.notification = QtWidgets.QLabel(self.centralwidget)
        self.notification.setGeometry(QtCore.QRect(260, 0, 541, 41))
        self.notification.setStyleSheet("color: rgb(239, 41, 41);")
        self.notification.setText("")
        self.notification.setAlignment(QtCore.Qt.AlignCenter)
        self.notification.setObjectName("notification")
        self.message = QtWidgets.QLineEdit(self.centralwidget)
        self.message.setGeometry(QtCore.QRect(260, 550, 471, 31))
        self.message.setObjectName("message")
        self.username = QtWidgets.QLabel(self.centralwidget)
        self.username.setGeometry(QtCore.QRect(95, 5, 160, 30))
        self.username.setText("")
        self.username.setObjectName("username")
        self.message_box.raise_()
        self.search_input.raise_()
        self.search_button.raise_()
        self.contacts.raise_()
        self.reg_log_dialog.raise_()
        self.send.raise_()
        self.button_connect.raise_()
        self.search_list.raise_()
        self.notification.raise_()
        self.message.raise_()
        self.username.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.reg_log_dialog.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.search_button.setText(_translate("MainWindow", "Find"))
        self.input_login.setPlaceholderText(_translate("MainWindow", "input username"))
        self.input_password.setPlaceholderText(_translate("MainWindow", "input password"))
        self.label_login.setText(_translate("MainWindow", "Login"))
        self.label_password.setText(_translate("MainWindow", "Password"))
        self.reg_log_dialog.setTabText(self.reg_log_dialog.indexOf(self.login_dialog), _translate("MainWindow", "Login"))
        self.reg_label_login.setText(_translate("MainWindow", "Login"))
        self.reg_login_input.setPlaceholderText(_translate("MainWindow", "input username"))
        self.reg_label_passwd.setText(_translate("MainWindow", "Password"))
        self.reg_passwd_input.setPlaceholderText(_translate("MainWindow", "input password"))
        self.reg_passwd_input_2.setPlaceholderText(_translate("MainWindow", "input password"))
        self.reg_label_passwd_2.setText(_translate("MainWindow", "Confirm"))
        self.reg_log_dialog.setTabText(self.reg_log_dialog.indexOf(self.reg_dialog), _translate("MainWindow", "Register"))
        self.send.setText(_translate("MainWindow", "Send"))
        self.button_connect.setText(_translate("MainWindow", "connect"))
