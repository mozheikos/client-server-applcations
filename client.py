from datetime import datetime
import sys

from base import BaseTCPSocket
from common.config import Action, DEFAULT_ENCODING
from common.utils import get_cmd_arguments
from decorators import log
from templates.templates import Request, User, Response


class TCPSocketClient(BaseTCPSocket):
    
    username: str = None
    password: str = None

    is_connected = False
    
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
        
        self.username = username
        self.password = password
        
        if connect:
            self.connect()
    
    @log
    def connect(self):
        
        self.connection.connect((self.host, self.port))
        self.is_connected = True
    
    @log
    def get_method(self, action):
        methods = {
            'presence': self.get_presence
        }
        return methods.get(action, None)
    
    @log
    def get_presence(self):
        user: User = User(
            account_name=self.username,
            status='online'
        )
        request = Request(
            action=Action.presence,
            time=datetime.now().isoformat(),
            user=user
        )
        return request.json(exclude_none=True, ensure_ascii=False).encode(DEFAULT_ENCODING)
    
    @log
    def send_request(self, request):
        self.connection.send(request)
    
    @log
    def request(self, action, message: str = None):
        handler = self.get_method(action)

        assert handler, 'Action not allowed'
        assert self.is_connected, 'Not connected'

        request = handler()
        self.send_request(request)
        self.receive()
    
    @log
    def receive(self):
        received = self.connection.recv(self.buffer_size)
        
        assert received, 'No data received'
        response = Response.parse_raw(received)
        print(response.json(exclude_none=True, ensure_ascii=False, indent=4))
        
@log
def main():
    with TCPSocketClient(host=cl_host, port=cl_port, username='test user', password='password', connect=True) as client:
        client.request('presence')

if __name__ == '__main__':

    cl_host, cl_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    if cl_host == '':
        print("Не задан адрес сервера")
        exit(1)
    main()
