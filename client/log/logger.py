import logging
import os
from logging import handlers

"""Оставлю только логгер в файл. В качестве хэндлера установил RotateFileHandler, так как в режиме DEBUG лог растет
ОЧЕНЬ быстро, за 2 вечера выполнения дз - больше гигабайта!!! Ну и уровень сделал ERROR"""

PATH = os.getcwd()
if 'log_journal' not in os.listdir(PATH):
    os.mkdir(f"{PATH}/log_journal")


logger = logging.getLogger('client_logger')

formatter = logging.Formatter("%(asctime)-2s %(levelname)-4s: %(message)s")

file_handler = handlers.RotatingFileHandler(
    filename=f"{PATH}/log_journal/log.log",
    maxBytes=10240,
    backupCount=10,
    encoding='utf-8'
    )

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)

logger.addHandler(file_handler)

logger.setLevel(logging.ERROR)
