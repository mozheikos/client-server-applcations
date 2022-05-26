import json
from unittest import TestCase, main

from client import TCPSocketClient
from templates.templates import Request
from common.config import Action
from common.utils import get_cmd_arguments

"""
Перед запуском тестов необходимо запустить сервер.
Наверное маловато, но так и не придумал как проверить некоторые методы,
которые взаимосвязаны между собой. Постарался компенсировать применением
разных assert, чтоб разнообразнее было
"""


class TestServer(TestCase):

    def setUp(self) -> None:
        self.host = 'localhost'
        self.port = 7777
        self.username = 'test'
        self.password = 'test'
        self.client_socket = TCPSocketClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            connect=True
        )
        
    def tearDown(self) -> None:
        self.client_socket.shutdown()

    def test_server_response_ok_status(self):
        action = 'presence'
        response = self.client_socket.request(action)
        self.assertEqual(response.response, '200 OK')

    def test_server_response_bad_request_status(self):
        action = 'invalid action'
        request_body = {
            'action': action,
            'time': 16465421,
            'user': {
                'account_name': self.username,
                'status': 'online'
            }
        }
        request = json.dumps(request_body, ensure_ascii=False).encode('unicode-escape')
        response = self.client_socket.send_request(request)
        self.assertEqual(response.response, '400 Bad Request')
        

class TestClient(TestCase):
    def setUp(self):
        self.host = 'localhost'
        self.port = 7777
        self.username = 'test'
        self.password = 'test'
        self.client_socket = TCPSocketClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            connect=False
        )
        self.client_socket.connect()
    
    def tearDown(self) -> None:
        self.client_socket.shutdown()
    
    def test_get_method_valid(self):
        method = self.client_socket.get_method('presence')
        self.assertIsNotNone(method)
    
    def test_get_method_invalid(self):
        method = self.client_socket.get_method('invalid action')
        self.assertIsNone(method)
    
    def test_get_presence(self):
        presence = Request.parse_raw(self.client_socket.get_presence())
        self.assertEqual(presence.action, Action.presence)
    
    def test_send_request(self):
        action = 'presence'
        request_body = {
            'action': action,
            'time': 16465421,
            'user': {
                'account_name': self.username,
                'status': 'online'
            }
        }
        request = json.dumps(request_body, ensure_ascii=False).encode('unicode-escape')
        response = self.client_socket.send_request(request)
        self.assertEqual(response.response, '200 OK')
    
    def test_request_valid_action(self):
        action = 'presence'
        response = self.client_socket.request(action)
        self.assertEqual(response.response, '200 OK')
    
    def test_request_invalid_action(self):
        action = 'invalid_action'
        self.assertRaises(
            AssertionError,
            self.client_socket.request, action
        )
    
    def test_receive(self):
        request = self.client_socket.get_presence()
        self.client_socket.connection.send(request)
        response = self.client_socket.receive()
        self.assertEqual(
            response.response, '200 OK'
        )


class TestUtils(TestCase):
    def setUp(self) -> None:
        self.valid_args = ['-h', 'localhost', '-p', 7777]
        self.invalid_args = ['-h', 'localhost', '-p']
        self.partial_args = ['-h', 'localhost']
    
    def test_get_args_valid(self):
        args = get_cmd_arguments(self.valid_args)
        self.assertTupleEqual(args, ('localhost', 7777))
    
    def test_get_args_valid_partial(self):
        args = get_cmd_arguments(self.partial_args)
        self.assertTupleEqual(args, ('localhost', 7777))
    
    def test_get_args_invalid(self):
        self.assertRaises(
            AttributeError,
            get_cmd_arguments,
            self.invalid_args
        )
        
    
if __name__ == '__main__':
    main()
