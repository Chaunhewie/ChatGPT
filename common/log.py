import logging
import os
import sys
from logging import handlers


def _get_logger():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    log = logging.getLogger('logs')
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(filename)s:%(lineno)d - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    # 文件日志
    file_handler = handlers.TimedRotatingFileHandler('logs/ChatGPT', when='d')
    file_handler.setFormatter(formatter)

    # 控制台日志
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(formatter)

    log.addHandler(file_handler)
    log.addHandler(console_handle)
    return log


# 日志句柄
logger = _get_logger()
