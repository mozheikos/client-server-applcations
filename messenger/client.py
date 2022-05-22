import socket
import json
from datetime import datetime
import sys

from common.config import HOST, PORT, BUFFER_SIZE
from common.utils import get_cmd_arguments

def send_presence(client: socket.socket, account: str) -> None:

    action = 'presence'
    status = 'connect'
    request_timestamp = str(datetime.now())

    request_template = {
        'action': action,
        'time':request_timestamp,
        'user':{
            'account_name': account,
            'status': status
        }
    }

    request = json.dumps(request_template, ensure_ascii=False).encode('unicode-escape')
    client.send(request)


def handle_server_response(client: socket.socket) -> str:

    response = client.recv(BUFFER_SIZE).decode('unicode-escape')
    message = json.loads(response)
    client.close()

    return message


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client.connect((host, port))

    account = 'test'
    send_presence(client=client, account=account)

    message = handle_server_response(client=client)
    print(message)


if __name__ == '__main__':

    host, port = get_cmd_arguments(cmd_line_args=sys.argv[1:])
    main()
