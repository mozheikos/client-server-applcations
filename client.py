from collections import deque
from datetime import datetime
import os
from queue import Queue
import sys
from time import sleep
from threading import Thread, Lock

from base import BaseTCPSocket
from common.config import Action, DEFAULT_ENCODING, Status, StopSendingError
from common.utils import get_cmd_arguments
from decorators import log
from templates.templates import Request, User, Response, Message


class TCPSocketClient(BaseTCPSocket):
    
    user: User
    
    is_connected = False
    
    inbox = Queue()
    outbox = Queue()
    action = None
    chat_stop = False
    chat = {}
    
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
    
    def shutdown(self):
        self.quit()
        super(TCPSocketClient, self).shutdown()
    
    @log
    def connect(self):
        
        self.connection.connect((self.host, self.port))
        self.send_presence()
        if self.receive():
            print(f'Connected {self.user.account_name}')
            self.is_connected = True

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
    def send_presence(self):
    
        request = Request(
            action=Action.presence,
            time=datetime.now().isoformat(),
            user=self.user
        )
        request = request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING)
        self.send_request(request)

    @log
    def send_request(self, request):
        self.connection.send(request)
        return True
    
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
    def receive_message(self):
        """Put new inbox message to queue"""
        # lock = Lock()
        while self.is_connected:
            # with lock:
            data = self.connection.recv(self.buffer_size)
            
            if data:
                message = Request.parse_raw(data)
                if message.action == Action.msg:
                    self.inbox.put(message)
                elif message.action == Action.server_shutdown:
                    self.is_connected = False
            else:
                self.is_connected = False
    
    @log
    def send_message(self):
        """Get outbox message from queue and send it to server"""
        # lock = Lock()
        while self.is_connected:
            # with lock:
            request = self.outbox.get(block=True)
            result = self.send_request(request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
            if not result:
                self.is_connected = False
    
    @log
    def get_outbox_message(self, to: str):
        """Get message from user and put it to queue for send"""
        # lock = Lock()
        os.system('clear')
        print(f'Chat with {to}')
        chat_history = Thread(target=self.print_message_to_chat, name='chat', kwargs={'from_': self.action},
                              daemon=True)
        chat_history.start()
        while self.is_connected:
            # with lock:
            contact = self.chat.get(to, None)
            text = input()
            if text == '/exit':
                self.action = None
                self.chat_stop = True
                break
            elif not len(text) or len(text) > 300:
                continue
            message = Message(to=to, from_=self.user.account_name, message=text)
            request = Request(action=Action.msg, time=datetime.now().isoformat(), user=self.user, data=message)
            self.outbox.put(request)
            if contact:
                contact['was_read'].append(request)
            else:
                self.chat[to] = {}
                self.chat[to]['was_read'] = [request]
    
    @log
    def get_message_from_queue(self):
        """Get message from inbox queue and put it to chat dictionary sort by 'from' username"""
        lock = Lock()
        while self.is_connected:
            # with lock:
            new: Request
            new = self.inbox.get(block=True)
            user = new.data.from_
            contact = self.chat.get(user, None)
            if contact:
                contact['new'].put(new)
            else:
                self.chat[user] = {}
                self.chat[user]['new'] = Queue()
                self.chat[user]['new'].put(new)
                self.chat[user]['was_read'] = []
    
    @log
    def print_message_to_chat(self, from_: str):
        lock = Lock()
        contact = self.chat.get(from_, None)
        if not contact:
            self.chat[from_] = {}
            self.chat[from_]['new'] = Queue()
            self.chat[from_]['was_read'] = []
            contact = self.chat[from_]
        mess: Request
        new_mess: Request
        # os.system('clear')
        for mess in contact['was_read']:
            print(f"{mess.time} {mess.data.from_}: {mess.data.message}")
        while not self.chat_stop:
            while not contact['new'].empty():
                # with lock:
                new_mess = contact['new'].get()
                print(f"{new_mess.time} {from_}: {new_mess.data.message}")
                contact['was_read'].append(new_mess)
    
    @log
    def print_menu(self):
        # lock = Lock()
        # while not self.action:
        #     with lock:
        os.system('clear')
        rows = ''
        for username, contact in self.chat.items():
            row = f"{username} ({len(contact['new'])})"
            rows += row + '\n'
        menu = f"{rows}\ninput username for chat with (if user not in list - will start new one)" \
               f"\ntype < /exit > for Exit\n"
        print(menu)
        # sleep(5)
    
    @log
    def request(self, action):
        handler = self.get_method(action)

        assert handler, 'Action not allowed'
        assert self.is_connected, 'Not connected'

        handler()
    
    @log
    def run(self):
        
        send = Thread(target=self.send_message, name='send', daemon=True)
        receive = Thread(target=self.receive_message, name='receive', daemon=True)
        check_inbox = Thread(target=self.get_message_from_queue, name='check_inbox', daemon=True)
        send.start()
        sleep(0.1)
        receive.start()
        sleep(0.1)
        check_inbox.start()
        sleep(0.1)
        # menu = Thread(target=self.print_menu, name='menu', daemon=True)
        while True:
            # menu.start()
            self.print_menu()
            self.action = input()
            if self.action == "/exit":
                break
            
            self.get_outbox_message(to=self.action)
            # write_mess = Thread(target=self.get_outbox_message, name='write', kwargs={'to': self.action}, daemon=True)
            # write_mess.start()
   
            
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
                        # action = 0
                        # while action not in ('1', '2'):
                        #     os.system('clear')
                        #     action = input('1. send\n2. receive\n')
                        # os.system('clear')
                        # action = int(action)
                        # if action == 1:
                        #     print(f'Sending messages, user:  {username}')
                        #     mode = Action.msg
                        # else:
                        #     print(f"Receiving messages, user: {username}")
                        #     mode = Action.recv
                        # while client.is_connected:
                        #     try:
                        #         client.request(mode)
                        #     except StopSendingError:
                        #         break
                        client.run()
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
