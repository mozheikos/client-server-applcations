from datetime import datetime
import sys

from pydantic import ValidationError

from base import BaseTCPSocket
from common.config import Action, DEFAULT_ENCODING
from common.utils import get_cmd_arguments
from log.client_log import logger
from templates.templates import Request, User, Response


class TCPSocketClient(BaseTCPSocket):
    
    username: str = None
    password: str = None

    is_connected = False
    
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
        
        logger.debug("Client initialization OK")
        if connect:
            self.connect()
    
    def connect(self):
        try:
            self.connection.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            logger.error(e)
        else:
            logger.info(f'Connected on {self.host}:{self.port}')
            self.is_connected = True
    
    def get_method(self, action):
        methods = {
            'presence': self.get_presence
        }
        return methods.get(action, None)
    
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
    
    def send_request(self, request):
        self.connection.send(request)

        logger.debug("Message send OK")
        return self.receive()
    
    def request(self, action, message: str = None):
        handler = self.get_method(action)
        try:
            assert handler, 'action not allowed'
            assert self.is_connected, 'Not connected'

            logger.debug("Handler method get OK")
            
            request = handler()
            logger.debug(f"{handler.__name__} OK")

            response = self.send_request(request)

        except AssertionError as e:
            logger.error(f"Message don't sent. Reason: {e}")
            return
        
        except ValidationError as e:
            logger.error("Invalid server response")
            return
        
        return response
    
    def receive(self):
        received = self.connection.recv(self.buffer_size)

        logger.debug("Data receive OK")
        response = Response.parse_raw(received)
        return response


def main():
    with TCPSocketClient(host=cl_host, port=cl_port, username='test user', password='password', connect=True) as client:
        result = client.request('presence')
        if result:
            logger.info(f"Response {result.response}")
            print(result.json(exclude_none=True, ensure_ascii=False, indent=4))


if __name__ == '__main__':

    cl_host, cl_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    if cl_host == '':
        print("Не задан адрес сервера")
        exit(1)
    main()
