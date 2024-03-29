from common.config import settings
import hashlib


def get_hashed_password(password: str) -> str:
    salt = hashlib.sha256(settings.SALT.encode()).hexdigest()

    return hashlib.sha256((salt + password).encode()).hexdigest()


def generate_session_token(username: str) -> str:
    """Generate session token"""

    salt = hashlib.sha256("salt".encode()).hexdigest()
    token = hashlib.sha256((salt + username).encode()).hexdigest()
    return token


def get_cmd_arguments(cmd_line_args: list) -> tuple:
    arguments = {
        '-h': settings.HOST,
        '-p': settings.PORT
    }

    # Получаем именованные параметры командной строки, присваиваем соответствующим значениям arguments
    cmd_length = len(cmd_line_args)

    if cmd_length and not cmd_length % 2:
        params_list = ([], [])
        for i in range(cmd_length):
            idx = i % 2
            params_list[idx].append(cmd_line_args[i])

        params = dict(zip(params_list[0], params_list[1]))

        for k, v in params.items():
            if k in arguments.keys():
                arguments[k] = v

    elif cmd_length:
        raise AttributeError('Invalid command line arguments')
    else:
        pass

    bind_host, bind_port = arguments['-h'], int(arguments['-p'])
    return bind_host, bind_port
