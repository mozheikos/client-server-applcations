from socket import socket, AddressFamily, SocketKind, AF_INET, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM

from common.config import settings

"""Решил что вот так будет совсем красиво. Сервер и клиент изначально представляют собой одно и то же - сокет, поэтому
часть параметров у них общая и часть методов класса соответственно тоже (создание объекта сокета, установка некоторых
параметров. Поэтому все общее я решил вынести в базовый класс"""


class BaseTCPSocket:

    host: str = settings.HOST
    port: int = settings.PORT
    
    address_family: AddressFamily = AF_INET
    socket_type: SocketKind = SOCK_STREAM
    
    buffer_size: int = settings.BUFFER_SIZE
    
    connection: socket = None
    
    def __init__(self, host, port, buffer):
        
        if host:
            assert isinstance(host, str), "Variable 'host' must be str"
            self.host = host
    
        if port:
            assert isinstance(port, int), "Variable 'port' must be int"
            self.port = port
    
        if buffer:
            assert isinstance(buffer, int), "Variable 'buffer' must be int"
            self.buffer_size = buffer
        self._connect()
        
    def _connect(self):
        self.connection = socket(self.address_family, self.socket_type)
        self.connection.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    
    def shutdown(self):
        self.connection.close()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
