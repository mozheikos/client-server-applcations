import datetime
import socket
import sys
from socketserver import BaseRequestHandler, TCPServer, StreamRequestHandler

from common.utils import get_cmd_arguments
from templates.models import Response, Request


# Класс обработчика. Пока унаследую от базового, в последующем, когда будем разбирать буфер
# при использовании сокета - лучше будет наследовать от StreamRequestHandler
class Handler(BaseRequestHandler):

    # Определю здесь допустимые методы. Так точно потом будет удобнее
    allowed_request_actions = (
        'presence',
        'register',  # этого нет в методичке, но если есть аутентификация - значит должна быть и регистрация
        'authenticate',
        'quit',
        'join',
        'leave',
        'msg'
    )
    # Специальный серверный метод опроса "живых" вынесу отдельно
    probe_action = 'probe'

    def __init__(self, request, client_address, server: TCPServer):
        self.message: str = ''
        super().__init__(request, client_address, server)

    def connect_accepted(self):
        """Метод ответа на запрос подключения"""

        timestamp = datetime.datetime.now()
        status_code = 200
        alert = 'Успешно'
        response = Response(
            response=status_code,
            time=timestamp,
            alert=alert
        )
        self.request.send(response.json(exclude_none=True, ensure_ascii=False).encode('unicode-escape'))
        print(f"response to {self.client_address[0]}:{self.client_address[1]} sent at {timestamp}")

    def setup(self) -> None:
        """Этот метод вызывается первым, здесь и примем сообщение"""

        self.message = self.request.recv(1024).decode('unicode-escape')

    def _get_method(self, action):
        """Словарь по мере разработки будет дополняться методами запроса и соответствующими методами их обработки"""
        methods = {
            'presence': self.connect_accepted
        }
        return methods[action]

    def handle(self) -> None:
        """Основной метод обработчика"""

        received = Request.parse_raw(self.message)

        """Благодаря методы handle_error серверного класса проверки можно делать через assert, 
        исключение обработается"""
        assert received.action in self.allowed_request_actions, '400, Method not allowed'

        print(f"connect from {self.client_address[0]}:{self.client_address[1]} accepted")
        handler_method = self._get_method(received.action)
        handler_method()


class MyServer(TCPServer):
    # определяем тип серверного протокола - IPv4
    address_family = socket.AF_INET

    # в коде класса True в данной переменной вызовет команду
    # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) - разрешаем переиспользовать адрес
    allow_reuse_address = True

    # устанавливаем тип протокола сокета - TCP (ремарка: параметр указывать в данном случае нет необходимости,
    # поскольку
    socket_type = socket.SOCK_STREAM

    # данный параметр указывает значение переменной для метода listen() - длину очереди
    # self.socket.listen(self.request_queue_size) - вызывается под капотом
    request_queue_size = 5

    def verify_request(self, request, client_address) -> bool:
        """Данный метод вызывается первым, некий аналог 'middleware на минималках', очень похоже на то,
            что здесь удобно проверить, кто стучится. Например, ip-адрес клиента, вдруг пиндос. Пока верну
            True всем.
        """

        return True

    def handle_error(self, request, client_address) -> None:
        """Обработчик исключений. Данный метод вызывается при возникновении исключения в ходе обработки запроса.
        После этого метода всегда вызывается shutdown_request, который закроет соединение"""
        import traceback
        exception, error = traceback.format_exc().splitlines()[-1].split(':', 1)
        if exception == 'AssertionError':
            """Все assert'ы прилетят сюда и будет сформирован ответ сервера с указанием ошибки"""
            status_code, error = error.split(", ")
            timestamp = datetime.datetime.now()
            response = Response(
                response=int(status_code),
                time=timestamp,
                error=error.strip()
            )
            request.send(response.json(exclude_none=True, ensure_ascii=False).encode('unicode-escape'))


if __name__ == '__main__':

    host, port = get_cmd_arguments(cmd_line_args=sys.argv[1:])

    with MyServer((host, port), Handler) as socket_server:
        print(f"server listen on {host if host else 'localhost'}:{port}")
        socket_server.serve_forever(0.5)
