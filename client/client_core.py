"""
Main functionality of client application
"""

import json
from collections import deque
from datetime import datetime
from time import sleep
from typing import Optional, Callable, Dict, Tuple

import rsa
from cryptography.fernet import Fernet

from client.database import ClientDatabase
from common.base import BaseTCPSocket
from common.config import settings
from common.exceptions import AlreadyExist
from templates.templates import Request, User, Message


class TCPSocketClient(BaseTCPSocket):
    """Client main class."""

    user: User
    gui = None
    is_connected = False
    chat: Dict[str, Dict[str, deque]] = {}
    found_contacts = {}

    def __init__(self, host: str = None, port: int = None, buffer: int = None, connect: bool = False):
        """
        Init
        :param host: str
        :param port: int
        :param buffer: int
        :param connect: bool - If True client socket connect after initialization
        """
        super().__init__(host, port, buffer)
        self.__pubkey, self.__privkey = self.__generate_keys()
        self.db: Optional[ClientDatabase] = None
        self.contacts_fetch = False
        self.messages_fetch = False
        self.auth_error = False
        self.server_key: Optional[rsa.PublicKey] = None
        if connect:
            self.connect()

    @staticmethod
    def __generate_keys() -> Tuple[rsa.PublicKey, rsa.PrivateKey]:
        """
        Generates pair RSA keys
        :return: Tuple(rsa.PublicKey, rsa.PrivateKey)
        """
        return rsa.newkeys(settings.RSA, poolsize=16)

    def get_handler(self, action) -> Callable:
        """
        Returns handler method to handle request in router
        :param action: str
        :return: Callable
        """
        methods = {
            settings.Action.presence: self._presence,
            settings.Action.register: self._register,
            settings.Action.auth: self._login,
            settings.Action.contacts: self._get_contacts,
            settings.Action.messages: self._get_history,
            settings.Action.msg: self._message,
            settings.Action.search: self._find_contact,
            settings.Action.add_chat: self._add_contact
        }
        return methods.get(action, None)

    def receive(self) -> None:
        """
        Main request router. Receives request and starts handler if action allowed
        :return:
        """
        while self.is_connected:

            data = self.connection.recv(self.buffer_size)
            if not data:
                continue

            try:
                received = self._decrypt(data)
            except rsa.pkcs1.DecryptionError:
                continue

            request: Request = Request.parse_raw(received)

            if request.status == settings.Status.unauthorized and request.action not in (
                    settings.Action.auth, settings.Action.register
            ):
                self.is_connected = False
                self._connect()
                self._authorization_error()

            else:
                handler = self.get_handler(request.action)
                assert handler, 'Action not allowed'

                handler(request)

    def _authorization_error(self):
        """
        Handler for authorization error. Stops router work. Emit auth_error
        :return:
        """
        self.auth_error = True
        self.gui.auth_error.emit()

    def quit(self):
        """
        Send message about client disconnecting to server
        :return:
        """
        request = Request(
            action=settings.Action.quit,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user if hasattr(self, 'user') else None
        )
        self.send_request(request)
        self.is_connected = False

    def connect(self):
        """
        Connecting to server
        :return:
        """
        try:
            self.connection.connect((self.host, self.port))
        except Exception as exception:
            raise exception
        else:
            key = json.loads(self.connection.recv(self.buffer_size).decode(settings.DEFAULT_ENCODING))
            self.server_key = rsa.PublicKey(*key)
            self.is_connected = True
            self.presence()

    def _decrypt(self, request: bytes) -> bytes:
        """
        Takes Request, encoded by key, returns bytes of decoded Request
        :param request: bytes
        :return: bytes
        """
        decoded_key, payload = request[:settings.FERNET], request[settings.FERNET:]

        cipher = rsa.decrypt(decoded_key, self.__privkey)

        cipher_key = Fernet(cipher)
        data = cipher_key.decrypt(payload)
        return data

    def _encrypt(self, request: Request) -> bytes:
        """
        Encrypt request. Takes Request, encode in with RSA and return bytes
        :param request: Request
        :return: bytes
        """
        cipher = Fernet.generate_key()
        cipher_key = Fernet(cipher)

        encoded_data = cipher_key.encrypt(
            request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING)
        )
        encoded_key = rsa.encrypt(cipher, self.server_key)

        return encoded_key + encoded_data

    def send_request(self, request: Request) -> None:
        """
        Send request
        :param request: Request
        :return:
        """
        self.connection.send(self._encrypt(request))

    def presence(self) -> None:
        """
        Send presence request
        :return:
        """
        request = Request(
            action=settings.Action.presence,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            data=[self.__pubkey.n, self.__pubkey.e]
        )
        self.send_request(request)

    def _presence(self, request: Request) -> None:
        """
        Handle presence response
        :param request: Request
        :return:
        """
        if request.status == settings.Status.ok:
            self.gui.connected.emit()
        else:
            self.quit()
            self.shutdown()
            self.is_connected = False

    def _register(self, request: Request) -> None:
        """
        Emit signal to GUI when registration failed
        :param request: Request
        :return:
        """
        self.gui.user_register_error.emit(request.data)

    def login(self, login: str, passwd: str, register: bool = False) -> None:
        """
        Send login request if register = False, else register request
        :param login: str
        :param passwd: str
        :param register: bool
        :return:
        """
        # Создаем базу данных именно здесь. Вынужденная мера, связанная с запуском нескольких клиентов
        # из одной директории (для прверки работы. В таком случае, для избежания коллизий данных,
        # необходимо создавать отдельную базу для каждого юзера, соответственно узнать ее название можно
        # только когда юзер введет логин. Можно было реализовать в одной базе, но тогда нужно добавлять
        # поляво все таблицы, указывающие какому пользователю принадлежит запись, а это дополнительный
        # фильтр при запросах, что снизит производительность
        self.db = ClientDatabase(login)
        request = Request(
            action=settings.Action.auth if not register else settings.Action.register,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=User(
                login=login,
                password=passwd
            )
        )
        self.send_request(request)

    def _login(self, request: Request):
        """
        Handle login response. Emit user_logged_in or user_wrong_creds
        :param request: Request
        :return:
        """
        if request.status == settings.Status.ok:
            self.user = User(
                id=request.data.id,
                login=request.data.login,
                verbose_name=request.data.verbose_name,
                token=request.data.token
            )
            self.auth_error = False
            self.gui.user_logged_in.emit()
        else:
            self.gui.user_wrong_creds.emit(request.data)

    def get_contacts(self):
        """
        Send request to fetch servers contact list for user
        :return:
        """
        request = Request(
            action=settings.Action.contacts,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user
        )
        self.send_request(request)

    def _get_contacts(self, request: Request):
        """
        Receive users contact list from server and saving it to database
        :param request: Request
        :return:
        """
        self.db.save_contacts(request.data)
        self.contacts_fetch = True

    def get_history(self):
        """
        Same as get_contacts, dut for message history
        :return:
        """
        request = Request(
            action=settings.Action.messages,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user
        )
        self.send_request(request)

    def _get_history(self, request: Request):
        """
        Same as _get_contacts
        :param request: Request
        :return:
        """
        self.db.save_messages(request)
        self.messages_fetch = True

    def get_server_data(self):
        """
        Initialize routing method. Fetch data about contacts and messages from server and then
        starts application initialization
        :return:
        """
        if self.auth_error:
            return

        self.get_contacts()
        while not self.contacts_fetch and not self.auth_error:
            sleep(0.1)

        if self.auth_error:
            return

        self.get_history()
        while not self.messages_fetch and not self.auth_error:
            sleep(0.1)

        if self.auth_error:
            return

        self.initialize()

    def initialize(self):
        """
        Local initialization. Fetch data from local database and put it into application variables.
        Emit initialized signal
        :return:
        """
        contacts = self.db.get_contacts()
        messages = self.db.get_messages()

        for contact in contacts:
            self.chat[contact.login] = {
                'new': deque(),
                'was_read': deque([
                    Request(
                        action=settings.Action.msg,
                        time=x.date.strftime(settings.DATE_FORMAT),
                        data=Message(
                            to=x.contact.login if x.kind == 'outbox' else self.user.login,
                            from_=x.contact.login if x.kind == 'inbox' else self.user.login,
                            encoding='utf-8',
                            message=x.text,
                            date=x.date.strftime(settings.DATE_FORMAT),
                        ),
                    ) for x in messages if x.contact.login == contact.login
                ])
            }
        self.gui.initialized.emit()

    def find_contact(self, login: str):
        """
        Send request to find contact by username
        :param login: str
        :return:
        """
        request = Request(
            action=settings.Action.search,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user,
            data=login
        )
        self.send_request(request)

    def _find_contact(self, request: Request):
        """
        Handle find response. Put response data in found list of contacts. Emit find_contact
        :param request: Request
        :return:
        """
        self.found_contacts = {x.login: x for x in request.data}
        self.gui.find_contact.emit(request.data)

    def add_contact(self, login: str):
        """
        After choosing contact to add, get contact data from founded and send request for
        adding contact in users contact list
        :param login: str
        :return:
        """
        contact = self.found_contacts.get(login)

        request = Request(
            action=settings.Action.add_chat,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user,
            data=contact,
        )
        self.send_request(request)

    def _add_contact(self, request: Request):
        """
        Handle add contact response. Saves contact to local database, if needed and put it to
        messenger contacts variable. Emit add_contact
        :param request: Request
        :return:
        """
        contact = request.data

        try:
            self.db.save_contact(contact)
        except AlreadyExist:
            ...

        if contact.login not in self.chat:
            self.chat[contact.login] = {}
            self.chat[contact.login]['new'] = deque()
            self.chat[contact.login]['was_read'] = deque()

        self.gui.add_contact.emit()

    def save_message(self, request: Request, kind: str):
        """
        Save message to database
        :param request: Request
        :param kind: str
        :return:
        """
        self.db.save_message(request, kind)

    def save_contact(self, contact: User):
        """
        Save contact to database
        :param contact: User
        :return:
        """
        self.db.save_contact(contact)

    def message(self, text: str, recipient: str):
        """
        Get outbox message from GUI and send it to server
        :param text: str
        :param recipient: str
        :return:
        """
        request = Request(
            action=settings.Action.msg,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user,
            data=Message(
                to=recipient,
                from_=self.user.login,
                message=text,
                date=datetime.now().strftime(settings.DATE_FORMAT)
            )
        )
        self.send_request(request)
        self.save_message(request, 'outbox')
        self.chat.get(recipient)['was_read'].append(request)

    def _message(self, request: Request):
        """
        Handle inbox messages. Save message in database and send signal to GUI. Emit new_message
        :param request: Request
        :return:
        """
        self.save_message(request, 'inbox')
        contact = self.chat.get(request.user.login, None)

        contact['new'].append(request)
        self.gui.new_message.emit(request.user.login)
