import os
import logging
import sys
from pathlib import Path

from common.config import DEBUG

PATH = Path(__file__).resolve().parent.parent
if 'log_journal' not in os.listdir(PATH):
    os.mkdir(f"{PATH}/log_journal")


logger = logging.getLogger('client_logger')

formatter = logging.Formatter("%(asctime)-2s %(levelname)-4s: %(message)s")

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(
    filename=f"{PATH}/log_journal/log.log",
    encoding='utf-8'
    )


stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

logger.setLevel(logging.DEBUG)
