import os
import logging
from logging import handlers
import sys
from pathlib import Path

from common.config import DEBUG

stdout_level = logging.DEBUG if DEBUG else logging.INFO
PATH = Path(__file__).resolve().parent.parent
if 'log_journal' not in os.listdir(PATH):
    os.mkdir(f"{PATH}/log_journal")

logger = logging.getLogger('server_logger')

formatter = logging.Formatter("%(asctime)-2s %(levelname)-4s: <%(module)s> %(message)s")

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = handlers.TimedRotatingFileHandler(
    filename=f"{PATH}/log_journal/server_log.log",
    when='midnight',
    interval=1,
    backupCount=5,
    encoding='utf-8'
    )

stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(stdout_level)

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

logger.setLevel(stdout_level)