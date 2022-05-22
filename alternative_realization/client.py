import datetime
import socket
import sys
from typing import Union

from common.utils import get_cmd_arguments
from common.config import BUFF_SIZE
from templates.models import Request, Response, User


# Решил сразу инкапсулировать работу в класс
class ClientSocket:

    # Инициализируем параметры подключения
    host = None
    port = None

    # Выставляем размер буфера чтения
    buff_size = BUFF_SIZE

    # Установим в эти переменные тип протокола и сокета
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM

    # В этом параметре будем хранить объект сокета
    _connection: Union[None, socket.socket] = None

    def __init__(self, host: str = None, port: int = None, buffer_size: int = None):

        self.host = host
        self.port = port
        if buffer_size:
            self.buff_size = buffer_size

        # Вызываю метод создания сокета
        self._connect()

    def _connect(self):
        """Данный метод создает сокет и помещает его в параметр экземпляра класса"""
        self._connection = socket.socket(self.address_family, self.socket_type)

    def connect(self):
        """Метод выполняет коннект для сокета"""
        self._connection.connect((self.host, self.port))

    def close(self):
        """Закрытие сокета"""
        self._connection.close()

    def send_presence(self, account: str, status: str):
        """Метод для отправки приветственного сообщения серверу"""
        action = 'presence'
        user = User(
            account_name=account,
            status='connect'
        )
        timestamp = datetime.datetime.now()
        request = Request(
            action=action,
            time=timestamp,
            type=status,
            user=user
        )
        self._connection.send(request.json(ensure_ascii=False).encode('unicode-escape'))
        self.wait_response()

    def wait_response(self):
        """Метод вызывается для получения ответа от сервера после отправки запроса"""
        received = self._connection.recv(self.buff_size)
        response = Response.parse_raw(received, encoding='unicode-escape')
        print(response.json(exclude_none=True, ensure_ascii=False, indent=4))

    # определяю методы для обеспечения возможности использования контекстного менеджера
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    # Создаем объект клиентского сокета, благодаря использованию контекстного менеджера соединение
    # устанавливается автоматически
    with ClientSocket(bind_host, bind_port) as sock:
        account_name = input("Input account name: ")
        status_request = 'status'
        sock.send_presence(account_name, status_request)


if __name__ == '__main__':

    bind_host, bind_port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    if bind_host == '':
        print("Не задан адрес сервера")
        exit(1)
    main()
