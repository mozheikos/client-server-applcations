import json
import sys
from collections import deque
from datetime import datetime
from socket import socket
from typing import Union, List, Optional

from pydantic import ValidationError

from base import TCPSocketServer
from common.config import settings
from common.utils import get_cmd_arguments, get_hashed_password
from databases import ServerDatabase
from decorators import log
from exceptions import UserAlreadyExist
from templates.templates import Response, Request, ConnectedUser


class RequestHandler:

    @log
    def __init__(self, request: socket, server: TCPSocketServer, clients: List[socket], database: ServerDatabase):
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
            settings.Action.auth: self.__handle_auth
        }
        return methods.get(self.message.action)
    
    def __handle_quit(self):
        address, port = self.request.getpeername()
        print(f"User {address}:{port} disconnected")
        self.__close_request()

    def __handle_register(self):
        """Регистрация нового пользователя"""
        try:
            user = self.db.create_user(self.message.user, self.request.getpeername()[0])
        except UserAlreadyExist:
            status = settings.Status.unauthorized
            alert = f'User {self.message.user.login} already exist'
            self.__send_response(status, alert, settings.Action.register)
        except AssertionError:
            status = settings.Status.unauthorized
            alert = f'Password required'
            self.__send_response(status, alert, settings.Action.register)
        else:
            self.__handle_auth()

    @log
    def __send_response(self, status: settings.Status, alert: str, action: settings.Action):

        response = Response(
            response=status,
            action=action,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            alert=alert
        )
        
        self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))
        print(f"Response {self.request.getpeername()[0]} - {response.response}")

    def __handle_presence(self):
        self.__send_response(settings.Status.ok, 'Success', settings.Action.presence)

    @log
    def __handle_auth(self):
        """Presense присылает логопасс. Функция проверяет существование пользователя и его пароль"""
        user = self.db.get_user(self.message.user.login)

        if not user or user.password != get_hashed_password(self.message.user.password):
            status = settings.Status.unauthorized
            alert = f'Wrong login and/or password'

        else:
            self.server.connected_users.setdefault(
                self.message.user.login,
                ConnectedUser(
                    user=self.message.user,
                    sock=[],
                    data=deque()
                )
            ).sock.append(self.request)
            status = settings.Status.ok
            alert = user.id

        self.__send_response(status=status, alert=alert, action=settings.Action.auth)
    
    @log
    def __handle_message(self):
        print(self.message.data)
        recipient = self.message.data.to
        to_send = self.server.connected_users.get(recipient, None)

        if to_send:
            for sock in to_send.sock:
                if sock in self.clients:
                    sock.send(
                        self.message.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))
                    
        else:
            response = Request(
                action=settings.Action.msg,
                time=datetime.now().strftime(settings.DATE_FORMAT),
                data=f"User {recipient} not connected"
            )
            self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))
    
    @log
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
    
    @log
    def handle_request(self):
        try:
            data = self.request.recv(self.server.buffer_size)
            
            assert data, 'No data received'
            
            self.message = Request.parse_raw(data)
            handler = self.get_method()

            assert handler, 'Action not allowed'
            handler()
            
        except ValidationError as e:
            self.__handle_error(e)
            raise e
        
        except AssertionError as e:
            self.__handle_error(e)
        
        except ConnectionError as e:
            self.__handle_error(e)

    @log
    def __close_request(self):

        self.request.close()
        if self.message.user:
            client = self.server.connected_users.get(self.message.user.login, None)
            if client:
                client.sock.remove(self.request)
        self.server.connected.remove(self.request)


@log
def main():
    with TCPSocketServer(handler=RequestHandler, host=srv_host, port=srv_port) as server:
        print(f"Server now listen on {srv_host if srv_host else 'localhost'}:{srv_port}")
        server.serve()


if __name__ == '__main__':
    srv_host, srv_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    main()
