from socket import socket
from datetime import datetime
from pydantic import ValidationError
import sys
from typing import Union
import json
from base import BaseTCPSocket
from common.config import Status, DEFAULT_ENCODING
from common.utils import get_cmd_arguments
from decorators import log
from templates.templates import Response, Request


class RequestHandler:

    message: Request = None

    @log
    def __init__(self, request: socket, client_address: tuple, server: BaseTCPSocket):
        self.request = request
        self.client_address = client_address
        self.server = server

    @log
    def get_method(self):

        methods = {
            'presence': self.handle_presence
        }
        return methods.get(self.message.action)

    @log
    def send_response(self, response: Response):

        self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
        print(f"Response {self.client_address[0]} - {response.response}")

    @log
    def handle_presence(self):

        current_time = datetime.now().isoformat()
        alert = 'Успешно'
        response = Response(
            response=Status.ok,
            time=current_time,
            alert=alert
        )
        self.send_response(response)

    def handle_error(self, error: Union[ValidationError, AssertionError]):
        if isinstance(error, ValidationError):
            error = json.loads(error.json())[0]
            msg = f"Invalid parameter: {', '.join(error['loc'])}"
        elif isinstance(error, AssertionError):
            msg = str(error)
            
        response = Response(
            response=Status.bad_request,
            time=datetime.now().isoformat(),
            error=msg
        )
        self.send_response(response)

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
            self.handle_error(e)
            raise e
        
        except AssertionError as e:
            self.handle_error(e)
            raise e
        

class TCPSocketServer(BaseTCPSocket):
    
    pool_size: int = 5
    
    request: Union[socket, None] = None

    @log
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
        
    @log        
    def bind_and_listen(self) -> None:
        """
            Initialize server socket. Calls on initialization of class automatically.
            Can be called manually, if start = False
        """

        self.connection.bind((self.host, self.port))
        self.connection.listen(self.pool_size)

    @log
    def serve(self):
        while True:

            self.request, address = self.connection.accept()
            
            print(f"{address[0]} connected")
            
            self.handle_request(address)
            self.close_request()
            
            print(f"Connection for {address[0]} closed")
    
    @log
    def handle_request(self, address):
        handler = RequestHandler(self.request, address, self)
        handler.handle_request()
                    
    @log                
    def close_request(self):
        self.request.close()


@log
def main():
    with TCPSocketServer(host=srv_host, port=srv_port) as server:
        print(f"Server now listen on {srv_host if srv_host else 'localhost'}:{srv_port}")
        server.serve()


if __name__ == '__main__':
    srv_host, srv_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    main()
