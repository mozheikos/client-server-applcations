import datetime
from select import select
from socket import socket, AddressFamily, SocketKind, AF_INET, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SHUT_RDWR
from typing import List

from common.config import settings
from databases import ServerDatabase
from decorators import log
from templates.templates import Request

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


class TCPSocketServer(BaseTCPSocket):
    pool_size: int = 5
    request_handler = None
    connected = []
    connected_users = {}

    @log
    def __init__(
            self,
            handler,
            host: str = None,
            port: int = None,
            buffer: int = None,
            pool_size: int = None,
            bind_and_listen: bool = True,
    ):
        """Initialize server class

        Args:
            host (str): address to listen (IPv4)
            port (int): port to listen
            buffer (int): size of receiving buffer, bytes
            pool_size (int): listening queue size
        """
        super(TCPSocketServer, self).__init__(host, port, buffer)

        self.gui = None
        self.request_handler = handler
        self.database = ServerDatabase()

        if pool_size:
            assert isinstance(pool_size, int), "Variable 'pool_size' must be int"
            self.pool_size = pool_size
        
        if bind_and_listen:
            self.bind_and_listen()
    
    @log
    def bind_and_listen(self) -> None:
        """
            Initialize server socket. Calls on initialization of class automatically.
            Can be called manually, if start = False
        """
        
        self.connection.bind((self.host, self.port))
        self.connection.listen(self.pool_size)
        self.connected.append(self.connection)
    
    def accept_connection(self):
        # Сделал немного иначе, без таймаута. При инициализации положил серверный сокет в список сокетов и проверяю в
        # селекте, если он готов для чтения - вызываю accept
        client, address = self.connection.accept()
        self.connected.append(client)
        print(f"{address[0]} connected")
    
    @log
    def serve(self):
        print('serving...')
        write = []
        while True:
            try:
                write: List[socket]
                read, write, _ = select(self.connected, self.connected, [])
                
                for sock in read:
                    if sock is self.connection:
                        self.accept_connection()
                    else:
                        self.handle_request(sock, write)
                        
            # KeyboardInterrupt возбуждается по CTRL + C, добавил обработку для корректного завершения и отправки
            # клиентам сигнала о том, что сервер недоступен
            except KeyboardInterrupt:
                for sock in write:
                    if sock is self.connection:
                        continue
                    request = Request(
                        action=settings.Action.server_shutdown,
                        time=datetime.datetime.now().strftime(settings.DATE_FORMAT)
                    )
                    try:
                        sock.send(request.json(exclude_none=True).encode(settings.DEFAULT_ENCODING))
                        sock.close()
                    except OSError:
                        continue
                self.connection.shutdown(SHUT_RDWR)
                self.shutdown()
                break
            
    @log
    def handle_request(self, client, writable):
        handler = self.request_handler(client, self, writable, self.database)
        handler.handle_request()
