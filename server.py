from socket import socket
from datetime import datetime
from pydantic import ValidationError
import sys
from typing import Union
import json
from base import BaseTCPSocket
from common.config import Status, DEFAULT_ENCODING
from common.utils import get_cmd_arguments
from templates.templates import Response, Request


class RequestHandler:

    message: Request = None

    def __init__(self, request: socket, client_address: tuple, server: BaseTCPSocket):
        self.request = request
        self.client_address = client_address
        self.server = server

    def get_method(self):

        methods = {
            'presence': self.handle_presence
        }
        return methods.get(self.message.action)

    def send_response(self, response: Response):
        current_time = datetime.now()

        self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))

        stdout = f"INFO: {current_time} - {self.client_address[0]} - {response.response}"
        return stdout

    def handle_presence(self):

        current_time = datetime.now().isoformat()
        alert = 'Успешно'
        response = Response(
            response=Status.ok,
            time=current_time,
            alert=alert
        )
        stdout = self.send_response(response)
        return stdout

    def handle_request(self):

        self.message = Request.parse_raw(self.request.recv(self.server.buffer_size))
        handler = self.get_method()
        return handler()


class TCPSocketServer(BaseTCPSocket):
    
    pool_size: int = 5
    
    request: Union[socket, None] = None

    def __init__(
            self,
            host: str = None,
            port: int = None,
            buffer: int = None,
            pool_size: int = None,
            bind_and_listen: bool = True
    ):
        """Initialize server class

        Args:
            host (str): address to listen (IPv4)
            port (int): port to listen
            buffer (int): size of receiving buffer, bytes
            pool_size (int): listening queue size
        """
        super(TCPSocketServer, self).__init__(host, port, buffer)
        
        if pool_size:
            assert isinstance(pool_size, int), "Variable 'pool_size' must be int"
            self.pool_size = pool_size

        if bind_and_listen:
            self.bind_and_listen()

    def bind_and_listen(self) -> None:
        """
            Initialize server socket. Calls on initialization of class automatically.
            Can be called manually, if start = False
        """

        self.connection.bind((self.host, self.port))
        self.connection.listen(self.pool_size)

    def serve(self):
        while True:

            self.request, address = self.connection.accept()
            try:
                stdout = self.handle_request(address)
                print(stdout)

            except ValidationError as error:
                """Ожидаю ValidationError, так как проверять данные буду средствами Pydantic,
                а он как раз возбуждает эту ошибку"""
                stderr = self.handle_error(error, address)
                print(stderr)
            
            except AssertionError as error:
                stderr = self.handle_error(error, address)
            
            except Exception as e:
                """Пока просто выведу в консоль"""
                print(e)

            finally:
                """Что бы ни было, после обработки соединение закрываем"""
                self.close_request()
                print(f"Connection for {address[0]} closed")
                
    def close_request(self):
        self.request.close()

    def handle_request(self, address):
        handler = RequestHandler(self.request, address, self)
        result = handler.handle_request()
        return result

    def handle_error(self, error: Union[ValidationError, AssertionError], address: tuple):
        error = json.loads(error.json())[0]
        msg = f"Invalid parameter: {', '.join(error['loc'])}"
        response = Response(
            response=Status.bad_request,
            time=datetime.now().isoformat(),
            error=msg
        ).json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING)
        self.request.send(response)
        stderr = f"ERROR: {datetime.now().isoformat()} - {address[0]} - {msg}"
        
        return stderr


def main():
    with TCPSocketServer(host=srv_host, port=srv_port) as server:
        print(f"Server now listen on {srv_host if srv_host else 'localhost'}:{srv_port}")
        server.serve()


if __name__ == '__main__':

    srv_host, srv_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    main()
