from collections import deque
from socket import socket
from datetime import datetime
from pydantic import ValidationError
import sys
from typing import Union, List
import json
from common.config import Status, DEFAULT_ENCODING, Action
from common.utils import get_cmd_arguments
from decorators import log
from templates.templates import Response, Request, Client, Message
from base import TCPSocketServer


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
    def send_response(self, status: Status, alert: str):
    
        current_time = datetime.now().isoformat()
        response = Response(
            response=status,
            time=current_time,
            alert=alert
        )
        
        self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
        print(f"Response {self.request.getpeername()[0]} - {response.response}")

    @log
    def handle_presence(self):
        connected: Client
        user = self.message.user.account_name
        connected = self.server.connected_users.get(user, None)
        
        if connected:
            connected.sock.append(self.request)
        else:
            connected = Client(
                user=self.message.user,
                sock=[self.request],
                data=deque()
            )
            self.server.connected_users[user] = connected
        
        self.send_response(status=Status.ok, alert='Success')
    
    @log
    def handle_message(self):
        to_send: Client
        print(self.message.user.account_name, self.message.data.message)
        recipient = self.message.data.to
        to_send = self.server.connected_users.get(recipient, None)
        if to_send:
            for sock in to_send.sock:
                if sock in self.clients:
                    sock.send(self.message.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
        else:
            response = Request(
                action=Action.msg,
                time=datetime.now().isoformat(),
                data=f"User {recipient} not connected"
            )
            self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
    
    @log
    def handle_error(self, error: Union[ValidationError, AssertionError, ConnectionError]):
        msg = ''
        if isinstance(error, ValidationError):
            error = json.loads(error.json())[0]
            msg = f"Invalid parameter: {', '.join(error['loc'])}"
        elif isinstance(error, AssertionError):
            msg = str(error)
        
        if str(error) == 'No data received' or isinstance(error, ConnectionError):
            self.close_request()
            
        else:
            self.send_response(Status.bad_request, msg)
    
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
        client: Client
        self.request.close()
        client = self.server.connected_users.get(self.message.user.account_name, None)
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
