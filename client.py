import os
import sys
from datetime import datetime
from queue import Queue
from threading import Thread, Lock
from time import sleep

from base import BaseTCPSocket
from common.config import settings
from common.utils import get_cmd_arguments
from databases import ClientDatabase
from decorators import log
from exceptions import AlreadyExist
from templates.templates import Request, User, Message


class TCPSocketClient(BaseTCPSocket):
    
    user: User
    gui = None
    is_connected = False
    
    inbox = Queue()
    outbox = Queue()
    action = None
    chat_stop = False
    chat = {}
    lock = Lock()
    to_print = True
    notify = (False, '')
    
    @log
    def __init__(
            self,
            host: str = None,
            port: int = None,
            buffer: int = None,
            connect: bool = False
    ):
        
        super(TCPSocketClient, self).__init__(host, port, buffer)
        self.db = ClientDatabase()
        self.initialized = False
        if connect:
            self.connect()

    def get_handler(self, action):
        methods = {
            settings.Action.presence: self._presence,
            settings.Action.register: self._register,
            settings.Action.auth: self._login,
            settings.Action.contacts: self._get_contacts,
            settings.Action.msg: self.send_message,
            settings.Action.recv: self.receive_message,
            settings.Action.quit: self.quit
        }
        return methods.get(action, None)

    def receive(self):

        while self.is_connected:

            received = self.connection.recv(self.buffer_size)
            assert received, 'No data received'

            request = Request.parse_raw(received)

            handler = self.get_handler(request.action)
            assert handler, 'Action not allowed'

            handler(request)

    def quit(self):
        request = Request(
            action=settings.Action.quit,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user if hasattr(self, 'user') else None
        )

        self.connection.send(request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))
        self.is_connected = False

    def shutdown(self):
        # self.quit()
        self.connection.close()

    def connect(self):
        try:
            self.connection.connect((self.host, self.port))
        except Exception as e:
            raise e
        else:
            self.is_connected = True
            self.presence()

    def presence(self):

        request = Request(
            action=settings.Action.presence,
            time=datetime.now().strftime(settings.DATE_FORMAT)
        )
        self.connection.send(request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))

    def _presence(self, request: Request):
        if request.status == settings.Status.ok:
            self.gui.connected.emit()
        else:
            self.quit()
            self.shutdown()
            self.is_connected = False

    def register(self, login: str, password: str):

        request = Request(
            action=settings.Action.register,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=User(
                login=login,
                password=password
            )
        )
        self.connection.send(request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))

    def _register(self, request: Request):
        self.gui.user_register_error.emit(request.data)

    def login(self, login: str, passwd: str):

        request = Request(
            action=settings.Action.auth,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=User(
                login=login,
                password=passwd
            )
        )
        self.connection.send(request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))

    def _login(self, request: Request):

        if request.status == settings.Status.ok:
            self.user = User(
                id=request.data.id,
                login=request.data.login,
                verbose_name=request.data.verbose_name
            )
            self.gui.user_logged_in.emit()
        else:
            self.gui.user_wrong_creds.emit(request.data)

    def get_contacts(self):
        request = Request(
            action=settings.Action.contacts,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user
        )
        self.connection.send(request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))

    def _get_contacts(self, request: Request):
        self.db.save_contacts(request.data, self.user.login)
        self.initialize()

    def initialize(self):
        contacts = self.db.get_contacts(owner=self.user.login)
        messages = self.db.get_messages(owner=self.user.login)

        for contact in contacts:
            self.chat[contact.login] = {
                'new': Queue(),
                'was_read': [
                    Request(
                        action=settings.Action.msg,
                        time=x.date.strftime(settings.DATE_FORMAT),
                        data=Message(
                            to=x.contact.login if x.kind == 'outbox' else self.user.login,
                            from_=x.contact.login if x.kind == 'inbox' else self.user.login,
                            encoding='utf-8',
                            message=x.text,
                            date=x.date.strftime(settings.DATE_FORMAT),
                        ),
                    ) for x in messages if x.contact.login == contact.login
                ]
            }
        self.initialized = True

    def find_contact(self, login):
        request = Request(
            action=settings.Action.search,
            time=datetime.now().strftime(settings.DATE_FORMAT),
            user=self.user,
            data=User(login=login)
        )
        self.connection.send(request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))

    def receive_contact(self, result: Request):
        if result.status == settings.Status.ok:
            contact = result.data
            try:
                self.db.save_contact(contact, owner=self.user.login)
            except AlreadyExist:
                ...
            if contact.login not in self.chat.keys():
                self.chat[contact.login] = {}
                self.chat[contact.login]['new'] = Queue()
                self.chat[contact.login]['was_read'] = []
        else:
            print(f'{result.data} Press <Enter>')
            input()
        self.to_print = True

    def get_contact(self, key):
        if key not in self.chat.keys():
            self.chat[key] = {}
            self.chat[key]['new'] = Queue()
            self.chat[key]['was_read'] = []
        return self.chat.get(key, None)

    def save_message(self, request: Request, kind: str):
        self.db.save_message(request, kind, self.user.login)

    def save_contact(self, request: Request):
        contact = User(
            id=request.user.id,
            login=request.user.login,
            verbose_name=request.user.verbose_name
        )
        self.db.save_contact(contact, self.user.login)

    @log
    def receive_message(self):
        """Put new inbox message to queue"""

        while self.is_connected:
            data = self.connection.recv(self.buffer_size)
            
            if data:
                message = Request.parse_raw(data)
                if message.action == settings.Action.msg:
                    if message.user.login not in self.chat.keys():
                        self.save_contact(message)
                    self.save_message(message, 'inbox')
                    self.inbox.put(message)
                elif message.action == settings.Action.server_shutdown:
                    self.is_connected = False
                elif message.action == settings.Action.search:
                    self.receive_contact(message)
                    
            else:
                self.is_connected = False
    
    @log
    def send_message(self):
        """Get outbox message from queue and send it to server"""

        while self.is_connected:
            
            request = self.outbox.get(block=True)
            self.send(
                request.json(exclude_none=True, ensure_ascii=False).encode(settings.DEFAULT_ENCODING))
            self.save_message(request, 'outbox')
            # if not result:
            #     self.is_connected = False
    
    @log
    def notification(self):
        
        if self.notify[0] and self.notify[1].endswith("not connected"):
            print(self.notify[1])
            
        elif self.action and self.notify[0] and self.action != self.notify[1]:
            print(f'New message from {self.notify[1]}')
    
    @log
    def get_outbox_message(self, to: str):
        """Get message from user and put it to queue for send"""
        
        if self.is_connected:
            contact = self.get_contact(to)

            os.system('clear')
            print(f'Chat with {to}. (input < /exit > for back to chat list)')
            self.chat_stop = False
            
            chat_history = Thread(target=self.print_message_to_chat, name='chat', kwargs={'from_': self.action},
                                  daemon=True)
            chat_history.start()
            
            while self.is_connected:
    
                text = input()
                if text == '/exit':
                    self.action = None
                    self.chat_stop = True
                    self.to_print = True
                    break

                elif not len(text) or len(text) > 300:
                    continue
                
                self.lock.acquire()

                message = Message(to=to, from_=self.user.login, message=text)
                request = Request(
                    action=settings.Action.msg,
                    time=datetime.now().strftime(settings.DATE_FORMAT),
                    user=self.user,
                    data=message
                )
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
            
            if isinstance(new.data, str):
                chat_name = new.data.replace('User ', '').replace(' not connected', '')
                user = new.data
                self.chat.pop(chat_name)
                
            else:
                user = new.data.from_
                contact = self.get_contact(user)
                contact['new'].put(new)
                
            self.notify = (True, user)
            self.to_print = True
            self.notification()
            
            self.lock.release()
    
    @log
    def print_message_to_chat(self, from_: str):
        """When in chat - prints all new messages and transfer it to 'was read' list"""
        mess: Request
        new_mess: Request

        contact = self.get_contact(from_)
        
        for mess in contact['was_read']:
            print(f"{mess.time} {mess.data.from_}: {mess.data.message}")
            
        while not self.chat_stop and self.is_connected:
            
            while not contact['new'].empty():
                
                with self.lock:
                    new_mess = contact['new'].get(block=True)
                    print(f"{new_mess.time} {from_}: {new_mess.data.message}")
                    contact['was_read'].append(new_mess)
                    self.to_print = True
    
    @log
    def print_menu(self):
        """When no action (user not in chat) - printing menu"""
        
        while not self.action and self.is_connected:
            
            if self.to_print:

                self.lock.acquire()
                
                rows = ''
                for username, contact in self.chat.items():
                    new_mess = contact['new'].qsize()
                    row = f"{username} ({new_mess})"
                    rows += row + '\n'
                if rows == '':
                    rows = 'No active chats\n'
                menu = f"{rows}\ninput username for chat with or '/add' to find" \
                       f"\ntype < /exit > for Exit\n"
                os.system('clear')
                print(menu)
                self.to_print = False
                
                self.lock.release()
    
    @log
    def run(self):
        
        send = Thread(target=self.send_message, name='send', daemon=True)
        receive = Thread(target=self.receive_message, name='receive', daemon=True)
        check_inbox = Thread(target=self.get_message_from_queue, name='check_inbox', daemon=True)
        send.start()
        sleep(0.3)
        receive.start()
        sleep(0.3)
        check_inbox.start()
        
        while self.is_connected:
            menu = Thread(target=self.print_menu, name='menu', daemon=True)
            menu.start()
            self.action = input()
            if self.action == "/exit":
                self.is_connected = False
                break
            elif self.action == '/add':
                os.system('clear')
                login = input('Input username:\n')
                self.find_contact(login)
                self.action = None
            elif self.action not in self.chat.keys():
                print(f"{self.action} not in contact list. Add first")
                input('Press <Enter>')
                self.action = None
            else:
                self.get_outbox_message(to=self.action)
            menu.join()
   
            
@log
def main():
    while True:
        option = 0
        while option not in ('1', '2'):
            os.system('clear')
            option = input('1. Login/Register\n2. Quit\nInput option: ')
        option = int(option)
        
        if option == 2:
            for i in range(1, 6, 1):
                print(f'\rExiting{"." * i}', end='')
                sleep(0.7)
            print()
            exit(0)
            
        elif option == 1:
            os.system('clear')
            action = input('1. Login\n2. Register\nInput option: ')

            with TCPSocketClient(host=cl_host, port=cl_port, connect=True) as client:
                os.system('clear')
                # client.connect()
                if client.is_connected:
                    result = ''
                    while result != 'success' and result != 'exit':

                        if action == '1':
                            result, action = client.auth(settings.Action.auth)
                        elif action == '2':
                            result, action = client.auth(settings.Action.register)
                    if result == 'exit':
                        for i in range(1, 6, 1):
                            print(f'\rExiting{"." * i}', end='')
                            sleep(0.7)
                        print()
                        exit(0)

                    client.initialize()
                    try:
                        client.run()
                        print('Disconnected from server (press <Enter> to continue)')
                        input()
                    except KeyboardInterrupt:
                        os.system('clear')
                        print('Disconnected from server (press <Enter> to continue)')
                        input()
                        exit(1)
                else:
                    print('Connection failed (press <Enter> to continue)')
                    input()
            del client
            
        else:
            continue
            

if __name__ == '__main__':

    cl_host, cl_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    if cl_host == '':
        print("Не задан адрес сервера")
        exit(1)
    main()
