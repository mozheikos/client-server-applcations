from enum import Enum


HOST = ''
PORT = 7777
BUFFER_SIZE = 1024
DEFAULT_ENCODING = 'unicode-escape'

DEBUG = True  # set False to disable DEBUG log messages


class Status(str, Enum):
    ok = '200 OK'
    bad_request = '400 Bad Request'
    forbidden = '403 Forbidden'
    unauthorized = '401 Unauthorized'


class Action(str, Enum):
    probe = 'probe'
    presence = 'presence'
    register = 'register'
    auth = 'authenticate'
    quit = 'quit'
    join = 'join'
    leave = 'leave'
    msg = 'msg'
