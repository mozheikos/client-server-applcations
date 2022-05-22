import socket
import json
from datetime import datetime
import sys

from common.config import BUFFER_SIZE
from common.utils import get_cmd_arguments


def send_response(client: socket.socket, response_template: dict) -> None:
    response = json.dumps(response_template, ensure_ascii=False).encode('unicode-escape')
    client.send(response)
    client.close()


def handle_presence_request(address: tuple, message: dict, current_time: datetime) -> dict:
    accepted_host, accepted_port = address
    print(f"connection from {accepted_host}:{accepted_port} accepted {current_time}")

    status_code = 200
    alert = f'Connect for user {message["user"]["account_name"]} accepted'
    response_template = {
        'response': status_code,
        'time': str(current_time),
        'alert': alert
    }
    return response_template


def handle_bad_request(error: Exception, message: dict, current_time: datetime) -> dict:
    status_code, error = str(error).split(', ')
    alert = f'Connect for user {message["user"]["account_name"]} rejected, reason: {error}'
    response_template = {
        'response': status_code,
        'time': str(current_time),
        'error': alert
    }
    return response_template


def serve(server_socket: socket.socket) -> None:
    template = dict()
    while True:
        sock, address = server_socket.accept()

        request = sock.recv(BUFFER_SIZE)
        message = json.loads(request.decode('unicode-escape'))
        current_time = datetime.now()
        try:
            assert message['action'] == 'presence', '400, method not allowed'
            template = handle_presence_request(address=address, message=message, current_time=current_time)
        
        except AssertionError as e:
            template = handle_bad_request(error=e, message=message, current_time=current_time)

        finally:
            send_response(client=sock, response_template=template)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    print(f"Server now listen on {host if host else 'localhost'}:{port}")
    serve(server_socket=server)


if __name__ == '__main__':

    host, port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    main()
