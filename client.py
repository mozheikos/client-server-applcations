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
    lock = Lock()
    to_print = True
    
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
        self.is_connected = False

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
    
    def get_contact(self, key):
        if key not in self.chat.keys():
            self.chat[key] = {}
            self.chat[key]['new'] = Queue()
            self.chat[key]['was_read'] = []
        return self.chat.get(key, None)
        
    @log
    def receive_message(self):
        """Put new inbox message to queue"""
        
        while self.is_connected:
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
        
        while self.is_connected:
            request = self.outbox.get(block=True)
            result = self.send_request(request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING))
            if not result:
                self.is_connected = False
    
    @log
    def get_outbox_message(self, to: str):
        """Get message from user and put it to queue for send"""
        
        contact = self.get_contact(to)

        os.system('clear')
        print(f'Chat with {to}')
        self.chat_stop = False
        chat_history = Thread(target=self.print_message_to_chat, name='chat', kwargs={'from_': self.action},
                              daemon=True)
        chat_history.start()
        
        while self.is_connected:

            text = input()
            if text == '/exit':
                self.action = None
                self.chat_stop = True
                break
            elif not len(text) or len(text) > 300:
                continue
            self.lock.acquire()
            message = Message(to=to, from_=self.user.account_name, message=text)
            request = Request(action=Action.msg, time=datetime.now().isoformat(), user=self.user, data=message)
            self.outbox.put(request)
            contact['was_read'].append(request)
            self.to_print = True
            self.lock.release()
        chat_history.join()
    
    @log
    def get_message_from_queue(self):
        """Get message from inbox queue and put it to chat dictionary sort by 'from' username"""

        new: Request

        while self.is_connected:
            if self.inbox.empty():
                continue
            self.lock.acquire()
            new = self.inbox.get(block=True)
            user = new.data.from_
            contact = self.get_contact(user)
            contact['new'].put(new)
            self.to_print = True
            self.lock.release()
    
    @log
    def print_message_to_chat(self, from_: str):
    
        mess: Request
        new_mess: Request
        
        contact = self.get_contact(from_)

        for mess in contact['was_read']:
            print(f"{mess.time} {mess.data.from_}: {mess.data.message}")
        while not self.chat_stop:
            
            while not contact['new'].empty():
                with self.lock:
                    new_mess = contact['new'].get(block=True)
                    print(f"{new_mess.time} {from_}: {new_mess.data.message}")
                    contact['was_read'].append(new_mess)
                    self.to_print = True
    
    @log
    def print_menu(self):
        
        while not self.action:
            if self.to_print:
                self.lock.acquire()
                rows = ''
                for username, contact in self.chat.items():
                    new_mess = contact['new'].qsize()
                    row = f"{username} ({new_mess})"
                    rows += row + '\n'
                if rows == '':
                    rows = 'No active chats\n'
                menu = f"{rows}\ninput username for chat with (if user not in list - will start new one)" \
                       f"\ntype < /exit > for Exit\n"
                os.system('clear')
                print(menu)
                self.to_print = False
                self.lock.release()
    
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
        # sleep(0.3)
        receive.start()
        # sleep(0.3)
        check_inbox.start()

        while True:
            menu = Thread(target=self.print_menu, name='menu', daemon=True)
            menu.start()
            self.action = input()
            if self.action == "/exit":
                break
            self.get_outbox_message(to=self.action)
            menu.join()
   
            
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
                        client.run()
                        print('Disconnected from server (press <Enter> to continue)')
                        input()
                    except KeyboardInterrupt:
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
