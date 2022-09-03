"""
Module defines base class for server and client applications
"""


from socket import socket, AddressFamily, SocketKind, AF_INET, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM

from common.config import settings


class BaseTCPSocket:
    """
    Base class. Creates TCP-socket instance, implement connect, shutdown, and context manager methods
    """

    host: str = settings.HOST
    port: int = settings.PORT
    
    address_family: AddressFamily = AF_INET
    socket_type: SocketKind = SOCK_STREAM
    
    buffer_size: int = settings.BUFFER_SIZE
    
    connection: socket = None
    
    def __init__(self, host, port, buffer):
        """
        Init
        :param host: str - ip-address IPv4 to listen or connect
        :param port: int - port to listen or connect
        :param buffer: int - buffer size, bytes
        """
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
        """Directly creates socket and set socket options"""

        self.connection = socket(self.address_family, self.socket_type)
        self.connection.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    
    def shutdown(self):
        """Close connection when called"""

        self.connection.close()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closing socket on shutdown"""

        self.shutdown()
