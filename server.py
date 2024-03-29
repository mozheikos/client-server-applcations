import json
from collections import deque
from datetime import datetime
from socket import socket
from typing import Union, List, Optional

import rsa
from cryptography.fernet import Fernet
from pydantic import ValidationError

from base import TCPSocketServer
from common.config import settings
from common.utils import generate_session_token, get_hashed_password
from databases import ServerDatabase
from decorators import log, login_required
from exceptions import AlreadyExist, NotExist, NotAuthorised
from templates.templates import Request, ConnectedUser, User, Message


class RequestHandler:

    @log
    def __init__(
            self,
            request: socket,
            server: TCPSocketServer,
            clients: List[socket],
            database: ServerDatabase,
            public_key: rsa.PublicKey,
            private_key: rsa.PrivateKey
    ):
        self.__private_key = private_key
        self.__public_key = public_key
        self.message: Optional[Request] = None
        self.request = request
        self.server = server
        self.clients = clients
        self.db = database

    @log
    def get_method(self):

        methods = {
            settings.Action.presence: self.__handle_presence,
            settings.Action.msg: self.__handle_message,
            settings.Action.quit: self.__handle_quit,
            settings.Action.register: self.__handle_register,
            settings.Action.auth: self.__handle_auth,
            settings.Action.contacts: self.__handle_contacts,
            settings.Action.search: self.__search,
            settings.Action.add_chat: self.__add_contact,
            settings.Action.del_chat: self.__del_contact,
            settings.Action.messages: self.__handle_messages
        }
        return methods.get(self.message.action)

    @login_required
    def __handle_messages(self):
        messages = self.db.get_message_history(self.message.user)
        status = settings.Status.ok
        action = settings.Action.messages
        alert = messages
        self.__send_response(status, alert, action)

    @login_required
    def __handle_contacts(self):
        user = self.message.user
        contacts = [User(id=x.id, login=x.login, verbose_name=x.verbose_name)
                    for x in self.db.get_user_contact_list(user)]
        status = settings.Status.ok
        action = settings.Action.contacts
        alert = contacts
        self.__send_response(status, alert, action)

    def __handle_quit(self):
        self.__close_request()

    def __handle_register(self):
        """Регистрация нового пользователя"""
        try:
            self.db.create_user(self.message.user)
        except AlreadyExist:
            status = settings.Status.unauthorized
            alert = f'User {self.message.user.login} already exist'
            self.__send_response(status, alert, settings.Action.register)
        except AssertionError:
            status = settings.Status.unauthorized
            alert = f'Password required'
            self.__send_response(status, alert, settings.Action.register)
        else:
            self.__handle_auth()

    def __send_response(
            self,
            status: settings.Status,
            alert: Union[Message, User, str, List[User], List[Message]],
            action: settings.Action
    ):

        response = Request(
            status=status,
            action=action,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            type='response',
            data=alert
        )

        data = self.__encrypt(response)

        self.request.send(data)
        self.server.gui.console_log.emit(f"Response {self.request.getpeername()[0]} - {response.status}")

    @login_required
    def __search(self):
        response = self.db.search(self.message.data)
        self.__send_response(settings.Status.ok, response, settings.Action.search)

    @login_required
    def __add_contact(self):

        try:
            self.db.create_chat(self.message.user, self.message.data)
        except AlreadyExist:
            ...

        to_send = self.server.connected_users.get(self.message.data.login, None)
        if to_send:
            request = Request(
                status=settings.Status.ok,
                action=settings.Action.add_chat,
                time=datetime.now().strftime(settings.DATE_FORMAT),
                type='request',
                data=self.message.user
            )

            to_send.sock.send(
                self.__encrypt(request, to_send.sock)
            )

        status = settings.Status.ok
        action = settings.Action.add_chat
        alert = self.message.data
        self.__send_response(status, alert, action)

    @login_required
    def __del_contact(self):
        try:
            self.db.delete_chat(self.message.user, self.message.data)
            status = settings.Status.ok
            alert = 'Success'
        except NotExist as e:
            status = settings.Status.bad_request
            alert = e

        action = settings.Action.del_chat
        self.__send_response(status, alert, action)

    def __handle_presence(self):

        key = rsa.PublicKey(*self.message.data)
        self.server.public_keys[self.request] = key

        ip = self.request.getpeername()
        date = datetime.now().strftime(settings.DATE_FORMAT)
        self.server.gui.user_connected.emit({'ip': ip[0], 'port': str(ip[1]), 'date': date})
        self.__send_response(settings.Status.ok, 'Success', settings.Action.presence)

    def __handle_auth(self):
        """Presense присылает логопасс. Функция проверяет существование пользователя и его пароль"""
        user = self.db.get_user(self.message.user.login)

        if not user or user.password != get_hashed_password(self.message.user.password):
            status = settings.Status.unauthorized
            alert = f'Wrong login and/or password'

        else:
            self.db.auth_user(user, self.request.getpeername()[0])

            token = generate_session_token(self.message.user.login)

            self.server.connected_users.setdefault(
                self.message.user.login,
                ConnectedUser(
                    user=self.message.user,
                    sock=self.request,
                    data=deque(),
                    token=token
                )
            )
            status = settings.Status.ok
            alert = User(id=user.id, login=user.login, verbose_name=user.verbose_name, token=token)

        self.__send_response(status=status, alert=alert, action=settings.Action.auth)

    @login_required
    def __handle_message(self):
        recipient = self.message.data.to
        to_send = self.server.connected_users.get(recipient, None)

        if to_send:
            self.db.create_message(self.message.data, True)
            to_send.sock.send(
                self.__encrypt(self.message, to_send.sock)
            )
                    
        else:
            self.db.create_message(self.message.data, False)

    def __handle_error(self, error: Union[ValidationError, AssertionError, ConnectionError]):
        msg = ''
        if isinstance(error, ValidationError):
            error = json.loads(error.json())[0]
            msg = f"Invalid parameter: {', '.join(error['loc'])}"
        elif isinstance(error, AssertionError):
            msg = str(error)
        
        if str(error) == 'No data received' or isinstance(error, ConnectionError):
            self.__close_request()
            
        else:
            self.__send_response(settings.Status.bad_request, msg, self.message.action)

    def __encrypt(self, data: Request, sock: socket = None) -> bytes:
        cipher = Fernet.generate_key()
        cipher_key = Fernet(cipher)

        user = sock or self.request

        user_key = self.server.public_keys.get(user)
        encoded_key = rsa.encrypt(cipher, user_key)

        encrypted_data = cipher_key.encrypt(
            data.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING)
        )
        result = encoded_key + encrypted_data
        return result

    def __decrypt(self, data: bytes) -> bytes:

        length = 64  # length of fernet key, encoded with rsa

        decoded_key, payload = data[:length], data[length:]
        cipher = rsa.decrypt(decoded_key, self.__private_key)

        cipher_key = Fernet(cipher)
        return cipher_key.decrypt(payload)

    def handle_request(self):
        try:
            data = self.request.recv(self.server.buffer_size)
            
            assert data, 'No data received'

            try:
                data = self.__decrypt(data)
            except rsa.pkcs1.DecryptionError:
                return

            self.message = Request.parse_raw(data)
            handler = self.get_method()

            assert handler, 'Action not allowed'
            handler()

        except NotAuthorised:
            self.__send_response(settings.Status.unauthorized, 'Incorrect token', action=self.message.action)
            self.__close_request()

        except ValidationError as e:
            self.__handle_error(e)
            raise e
        
        except AssertionError as e:
            self.__handle_error(e)
        
        except ConnectionError as e:
            self.__handle_error(e)

    @log
    def __close_request(self):
        address, port = self.request.getpeername()
        self.server.gui.console_log.emit(f"User {address}:{port} disconnected")
        self.server.gui.user_disconnected.emit((address, str(port)))

        self.request.close()
        if self.message and self.message.user:
            self.server.connected_users.pop(self.message.user.login, None)
        self.server.public_keys.pop(self.request, None)
        self.server.connected.remove(self.request)
