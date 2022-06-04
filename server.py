from socket import socket
from datetime import datetime
from pydantic import ValidationError
import sys
from typing import Union, List
import json
from base import BaseTCPSocket
from common.config import Status, DEFAULT_ENCODING
from common.utils import get_cmd_arguments
from decorators import log
from templates.templates import Response, Request
from base import TCPSocketServer
from select import select


class RequestHandler:

    message: Request = None
    server: TCPSocketServer

    @log
    def __init__(self, request: socket, server: TCPSocketServer, clients: List[socket]):
        self.request = request
        self.server = server
        self.clients = clients

    @log
    def get_method(self):

        methods = {
            'presence': self.handle_presence,
            'msg': self.handle_message,
            'quit': self.handle_quit
        }
        return methods.get(self.message.action)
    
    def handle_quit(self):
        print(f"User {self.message.user.account_name} disconnected")
        self.close_request()
    
    @log
    def send_response(self, response: Response):

        self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
        print(f"Response {self.request.getpeername()[0]} - {response.response}")

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
    
    def handle_message(self):
        
        for sock in self.clients:
            if sock is not self.server and sock is not self.request:
                sock.send(self.message.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
    
    def handle_error(self, error: Union[ValidationError, AssertionError]):
        msg = ''
        if isinstance(error, ValidationError):
            error = json.loads(error.json())[0]
            msg = f"Invalid parameter: {', '.join(error['loc'])}"
        elif isinstance(error, AssertionError):
            msg = str(error)
        
        if str(error) == 'No data received' or isinstance(error, ConnectionError):
            self.close_request()
            
        else:
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
        
        except ConnectionError as e:
            self.handle_error(e)

    @log
    def close_request(self):
        self.request.close()
        self.server.connected.remove(self.request)


@log
def main():
    with TCPSocketServer(handler=RequestHandler, host=srv_host, port=srv_port) as server:
        print(f"Server now listen on {srv_host if srv_host else 'localhost'}:{srv_port}")
        server.serve()


if __name__ == '__main__':
    srv_host, srv_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    main()
