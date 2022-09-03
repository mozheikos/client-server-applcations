"""
Server main processing module
"""


import datetime
import json
from collections import deque
from select import select
from socket import socket
from typing import Union, List, Optional, Tuple

import rsa
from cryptography.fernet import Fernet
from pydantic import ValidationError

from common.base import BaseTCPSocket
from common.config import settings
from common.decorators import login_required
from common.exceptions import AlreadyExist, NotExist, NotAuthorised
from common.utils import generate_session_token, get_hashed_password
from database import ServerDatabase
from templates.templates import Request, ConnectedUser, User, Message


class TCPSocketServer(BaseTCPSocket):
    """
    Server socket class. Receive requests and handle.
    """

    pool_size: int = 5
    request_handler = None
    connected = []
    connected_users = {}
    public_keys = {}

    def __init__(
            self,
            handler,
            host: str = None,
            port: int = None,
            buffer: int = None,
            pool_size: int = None,
            bind_and_listen: bool = True,
    ):
        """Initialize server class

        Args:
            host (str): address to listen (IPv4)
            port (int): port to listen
            buffer (int): size of receiving buffer, bytes
            pool_size (int): listening queue size
        """
        super(TCPSocketServer, self).__init__(host, port, buffer)

        self._public, self._private = self.__generate_keys()
        self.gui = None
        self.request_handler = handler
        self.database = ServerDatabase()

        if pool_size:
            assert isinstance(pool_size, int), "Variable 'pool_size' must be int"
            self.pool_size = pool_size

        if bind_and_listen:
            self.bind_and_listen()

    @staticmethod
    def __generate_keys() -> Tuple[rsa.PublicKey, rsa.PrivateKey]:
        """
        Generate RSA key pair
        :return: Tuple[rsa.PublicKey, rsa.PrivateKey]
        """
        return rsa.newkeys(settings.RSA, poolsize=16)

    def bind_and_listen(self) -> None:
        """
        Initialize server socket. Calls on initialization of class automatically.
        Can be called manually, if start = False
        :return:
        """

        self.connection.bind((self.host, self.port))
        self.connection.listen(self.pool_size)
        self.connected.append(self.connection)

    def accept_connection(self):
        """
        Accept new connection, append client socket to connected list, send rsa public key to client.
        Emit console_log
        :return:
        """

        client, address = self.connection.accept()
        self.connected.append(client)
        client.send(json.dumps([self._public.n, self._public.e]).encode(settings.DEFAULT_ENCODING))
        self.gui.console_log.emit(f"{address[0]} connected")

    def serve(self):
        """
        Main loop method.
        :return:
        """
        self.gui.console_log.emit(f'Serving at {self.host}:{self.port}')

        while True:
            read, _, _ = select(self.connected, [], [])

            for sock in read:
                if sock is self.connection:
                    self.accept_connection()
                else:
                    self.handle_request(sock)

    def handle_request(self, client: socket):
        """
        Create instance of handler class and call handle_request()
        :param client: socket
        :return:
        """

        handler = self.request_handler(client, self, self.database, self._public, self._private)
        handler.handle_request()


class RequestHandler:
    """
    Server handler class. Handle request and send response
    """
    def __init__(
            self,
            request: socket,
            server: TCPSocketServer,
            database: ServerDatabase,
            public_key: rsa.PublicKey,
            private_key: rsa.PrivateKey
    ):
        """
        Init
        :param request: socket - client socket to receive request data
        :param server: TCPServerSocket -  server class instance
        :param database: ServerDatabase - instance of server database handler
        :param public_key: rsa.PublicKey - server public key
        :param private_key: rsa.PrivateKey - server private key
        """

        self.__private_key = private_key
        self.__public_key = public_key
        self.message: Optional[Request] = None
        self.request = request
        self.server = server
        self.db = database

    def get_method(self):
        """
        Returns handler method to handle request in router
        :return: Callable
        """
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
        """
        Handle messages history request
        :return:
        """

        messages = self.db.get_message_history(self.message.user)
        status = settings.Status.ok
        action = settings.Action.messages
        alert = messages
        self.__send_response(status, alert, action)

    @login_required
    def __handle_contacts(self):
        """
        Handle get_contacts request
        :return:
        """

        user = self.message.user
        contacts = [User(id=x.id, login=x.login, verbose_name=x.verbose_name)
                    for x in self.db.get_user_contact_list(user)]
        status = settings.Status.ok
        action = settings.Action.contacts
        alert = contacts
        self.__send_response(status, alert, action)

    def __handle_quit(self):
        """
        Handle quit request
        :return:
        """
        self.__close_request()

    def __handle_register(self):
        """
        Handle register request. Creates new user. If success - directly call auth, else send Unauthorized
        response
        :return:
        """
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
        """
        Method to send response. Emit console_log
        :param status: settings.Status - response status
        :param alert: Union[Message, User, str, List[User], List[Message]] - data to send
        :param action: settings.Action
        :return:
        """

        response = Request(
            status=status,
            action=action,
            time=datetime.datetime.now().strftime(settings.DATE_FORMAT),
            type='response',
            data=alert
        )

        data = self.__encrypt(response)

        self.request.send(data)
        self.server.gui.console_log.emit(f"Response {self.request.getpeername()[0]} - {response.status}")

    @login_required
    def __search(self):
        """
        Handle search request
        :return:
        """

        response = self.db.search(self.message.data)
        self.__send_response(settings.Status.ok, response, settings.Action.search)

    @login_required
    def __add_contact(self):
        """
        Handle add contact request
        :return:
        """

        try:
            self.db.create_chat(self.message.user, self.message.data)
        except AlreadyExist:
            ...

        to_send = self.server.connected_users.get(self.message.data.login, None)
        if to_send:
            request = Request(
                status=settings.Status.ok,
                action=settings.Action.add_chat,
                time=datetime.datetime.now().strftime(settings.DATE_FORMAT),
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
        """
        Handle delete contact request
        :return:
        """
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
        """
        Handle presence. Receives clients public key and put it in server.public_keys collection.
        Emit user_connected
        :return:
        """

        key = rsa.PublicKey(*self.message.data)
        self.server.public_keys[self.request] = key

        ip = self.request.getpeername()
        date = datetime.datetime.now().strftime(settings.DATE_FORMAT)
        self.server.gui.user_connected.emit({'ip': ip[0], 'port': str(ip[1]), 'date': date})
        self.__send_response(settings.Status.ok, 'Success', settings.Action.presence)

    def __handle_auth(self):
        """
        Handle login request. Get user from database, compare hashed passwords. If success -
        generates session auth token and send it with response status 200, else -
        send response with status 401
        :return:
        """
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
        """
        Handle message request. Save message to history. If recipient is connected - send message, else
        mark message in database as not send
        :return:
        """
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
        """
        Error handling. On assertion, validation and connection error sends response with error text
        :param error: Union[ValidationError, AssertionError, ConnectionError]
        :return:
        """
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
        """
        Encrypt request with rsa key
        :param data: Request
        :param sock: socket, that represents user, whose public key will use to encrypt
        :return: bytes
        """

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
        """
        Decrypt request, represents bytestring
        :param data: bytes
        :return: bytes
        """

        decoded_key, payload = data[:settings.FERNET], data[settings.FERNET:]
        cipher = rsa.decrypt(decoded_key, self.__private_key)

        cipher_key = Fernet(cipher)
        return cipher_key.decrypt(payload)

    def handle_request(self):
        """
        Main request handler. Receives request, decrypt it and call handler by request action
        :return:
        """

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

    def __close_request(self):
        """
        Closes client socket
        :return:
        """

        address, port = self.request.getpeername()
        self.server.gui.console_log.emit(f"User {address}:{port} disconnected")
        self.server.gui.user_disconnected.emit((address, str(port)))

        self.request.close()
        if self.message and self.message.user:
            self.server.connected_users.pop(self.message.user.login, None)
        self.server.public_keys.pop(self.request, None)
        self.server.connected.remove(self.request)
