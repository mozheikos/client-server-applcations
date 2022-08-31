import json
from collections import deque
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Optional, Callable, Dict, Tuple

import rsa
from cryptography.fernet import Fernet

from base import BaseTCPSocket
from common.config import settings
from databases import ClientDatabase
from decorators import log
from exceptions import AlreadyExist
from templates.templates import Request, User, Message


class TCPSocketClient(BaseTCPSocket):
    
    user: User
    gui = None
    is_connected = False
    
    inbox = Queue()
    outbox = Queue()
    chat: Dict[str, Dict[str, deque]] = {}
    found_contacts = {}

    @log
    def __init__(
            self,
            host: str = None,
            port: int = None,
            buffer: int = None,
            connect: bool = False
    ):

        super(TCPSocketClient, self).__init__(host, port, buffer)
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
        return rsa.newkeys(512, poolsize=16)

    def get_handler(self, action) -> Callable:
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

    def receive(self):

        while self.is_connected:

            data = self.connection.recv(self.buffer_size)
            if not data:
                continue

            try:
                received = self._decrypt(data)
            except rsa.pkcs1.DecryptionError:
                continue

            request: Request = Request.parse_raw(received)

            if request.status == settings.Status.unauthorized:
                self.is_connected = False
                self._connect()
                self._authorization_error()
            else:
                handler = self.get_handler(request.action)
                assert handler, 'Action not allowed'

                handler(request)

    def _authorization_error(self):
        self.auth_error = True
        self.gui.auth_error.emit()

    def quit(self):
        request = Request(
            action=settings.Action.quit,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user if hasattr(self, 'user') else None
        )
        self.send_request(request)
        self.is_connected = False

    def connect(self):
        try:
            self.connection.connect((self.host, self.port))
        except Exception as e:
            raise e
        else:
            key = json.loads(self.connection.recv(self.buffer_size).decode(settings.DEFAULT_ENCODING))
            self.server_key = rsa.PublicKey(*key)
            self.is_connected = True
            self.presence()

    def _decrypt(self, request: bytes) -> bytes:
        length = 64  # length of fernet key, encoded with rsa
        decoded_key, payload = request[:length], request[length:]

        cipher = rsa.decrypt(decoded_key, self.__privkey)

        cipher_key = Fernet(cipher)
        data = cipher_key.decrypt(payload)
        return data

    def _encrypt(self, request: Request) -> bytes:

        cipher = Fernet.generate_key()
        cipher_key = Fernet(cipher)

        encoded_data = cipher_key.encrypt(
            request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING)
        )
        encoded_key = rsa.encrypt(cipher, self.server_key)

        return encoded_key + encoded_data

    def send_request(self, request: Request):
        self.connection.send(self._encrypt(request))

    def presence(self):

        request = Request(
            action=settings.Action.presence,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            data=[self.__pubkey.n, self.__pubkey.e]
        )
        self.send_request(request)

    def _presence(self, request: Request):
        if request.status == settings.Status.ok:
            self.gui.connected.emit()
        else:
            self.quit()
            self.shutdown()
            self.is_connected = False

    def _register(self, request: Request):
        self.gui.user_register_error.emit(request.data)

    def login(self, login: str, passwd: str, register: bool = False):
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
        request = Request(
            action=settings.Action.contacts,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user
        )
        self.send_request(request)

    def _get_contacts(self, request: Request):
        self.db.save_contacts(request.data)
        self.contacts_fetch = True

    def get_history(self):
        request = Request(
            action=settings.Action.messages,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user
        )
        self.send_request(request)

    def _get_history(self, request: Request):
        self.db.save_messages(request)
        self.messages_fetch = True

    def get_server_data(self):
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

    def find_contact(self, login):
        request = Request(
            action=settings.Action.search,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user,
            data=login
        )
        self.send_request(request)

    def _find_contact(self, request: Request):
        self.found_contacts = {x.login: x for x in request.data}
        self.gui.find_contact.emit(request.data)

    def add_contact(self, login: str):

        contact = self.found_contacts.get(login)

        request = Request(
            action=settings.Action.add_chat,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user,
            data=contact,
        )
        self.send_request(request)

    def _add_contact(self, request: Request):

        contact = request.data

        try:
            self.db.save_contact(contact)
        except AlreadyExist:
            ...

        if contact.login not in self.chat.keys():
            self.chat[contact.login] = {}
            self.chat[contact.login]['new'] = deque()
            self.chat[contact.login]['was_read'] = deque()

        self.gui.add_contact.emit()

    def save_message(self, request: Request, kind: str):
        self.db.save_message(request, kind)

    def save_contact(self, contact: User):
        self.db.save_contact(contact)

    def message(self, text: str, recipient: str):
        """Get outbox message from queue and send it to server"""

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

        self.save_message(request, 'inbox')
        contact = self.chat.get(request.user.login, None)

        contact['new'].append(request)
        self.gui.new_message.emit(request.user.login)
