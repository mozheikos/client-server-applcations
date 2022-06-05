import os
from datetime import datetime
import sys
from time import sleep

from base import BaseTCPSocket
from common.config import Action, DEFAULT_ENCODING, Status, StopSendingError
from common.utils import get_cmd_arguments
from decorators import log
from templates.templates import Request, User, Response, Message


class TCPSocketClient(BaseTCPSocket):
    
    user: User
    
    is_connected = False
    
    inbox = []
    
    @log
    def __init__(
            self,
            host: str = None,
            port: int = None,
            buffer: int = None,
            username: str = None,
            password: str = None,
            connect: bool = False
    ):
        assert username, "username is required"
        assert password, 'password is required'
        
        super(TCPSocketClient, self).__init__(host, port, buffer)
        
        self.user = User(
            account_name=username,
            password=password,
            status='online'
        )
        if connect:
            self.connect()
    
    @log
    def connect(self):
        
        self.connection.connect((self.host, self.port))
        self.send_presence()
        if self.receive():
            print(f'Connected {self.user.account_name}')
            self.is_connected = True
    
    @log
    def get_method(self, action):
        methods = {
            'presence': self.send_presence,
            'msg': self.send_message,
            'recv': self.receive_message,
            'quit': self.quit
        }
        return methods.get(action, None)
    
    @log
    def send_presence(self):
        
        request = Request(
            action=Action.presence,
            time=datetime.now().isoformat(),
            user=self.user
        )
        request = request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING)
        self.send_request(request)
    
    @log
    def receive_message(self):
        data = self.connection.recv(self.buffer_size)
        
        if data:
            message = Request.parse_raw(data)
            if message.action == Action.msg:
                print(f"{message.user.account_name}: {message.data.message}")
            elif message.action == Action.server_shutdown:
                self.is_connected = False
        else:
            self.is_connected = False
    
    @log
    def send_message(self):
        
        text = input('me: ')
        if text == '/exit':
            raise StopSendingError
        if not len(text):
            return
        if len(text) > 300:
            print(f'Message too long {len(text)}')
        message = Message(to='all', from_=self.user.account_name, message=text)
        request = Request(action=Action.msg, time=datetime.now().isoformat(), user=self.user, data=message)
        
        result = self.send_request(request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
        if not result:
            self.is_connected = False
    
    @log
    def send_request(self, request):
        self.connection.send(request)
        return True
        
    @log
    def request(self, action):
        handler = self.get_method(action)

        assert handler, 'Action not allowed'
        assert self.is_connected, 'Not connected'

        handler()
    
    @log
    def receive(self):
        received = self.connection.recv(self.buffer_size)
        
        assert received, 'No data received'
        response = Response.parse_raw(received)
        if response.response == Status.ok:
            return True
        return False
    
    @log
    def quit(self):
        request = Request(
            action=Action.quit,
            time=datetime.now().isoformat(),
            user=self.user
        )
        self.connection.send(
            request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING)
        )
        
        
@log
def main():
    while True:
        option = 0
        while option not in ('1', '2'):
            os.system('clear')
            option = input('1. Login\n2. Quit\nInput option: ')
        option = int(option)
        if option == 2:
            for i in range(1, 6, 1):
                print(f'\rExiting{"." * i}', end='')
                sleep(0.7)
            print()
            exit(0)
        elif option == 1:
            os.system('clear')
            print('Input your username and password:')
            username = input("username: ")
            password = input("password: ")
            with TCPSocketClient(host=cl_host, port=cl_port, username=username, password=password) as client:
                os.system('clear')
                client.connect()
                if client.is_connected:
                    try:
                        action = 0
                        while action not in ('1', '2'):
                            os.system('clear')
                            action = input('1. send\n2. receive\n')
                        os.system('clear')
                        action = int(action)
                        if action == 1:
                            print(f'Sending messages, user:  {username}')
                            mode = Action.msg
                        else:
                            print(f"Receiving messages, user: {username}")
                            mode = Action.recv
                        while client.is_connected:
                            try:
                                client.request(mode)
                            except StopSendingError:
                                break
                        print('Disconnected from server (press <Enter> to continue)')
                        input()
                    except KeyboardInterrupt:
                        client.request(Action.quit)
                        client.shutdown()
                        exit(1)
                else:
                    print('Connection failed (press <Enter> to continue)')
                    input()
        else:
            continue
            

if __name__ == '__main__':

    cl_host, cl_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    if cl_host == '':
        print("Не задан адрес сервера")
        exit(1)
    main()
