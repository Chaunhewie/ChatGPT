import logging
import os
import pathlib
import sys
from logging import handlers

log_path = pathlib.Path('./logs/')


def _get_logger(debug=False):
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    log = logging.getLogger("logs")
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    formatter = logging.Formatter('%(levelname)s %(asctime)s %(filename)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 文件日志
    file_handler = handlers.TimedRotatingFileHandler(os.path.join(log_path, 'ChatGPT'), when='h')
    file_handler.setFormatter(formatter)
    # 控制台日志
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(formatter)

    log.addHandler(file_handler)
    log.addHandler(console_handle)
    return log, file_handler


# 日志句柄与日志文件句柄
logger, log_file_handler = _get_logger(False)


def clean_log(remains_cnt=3):
    if remains_cnt < 1:
        logger.info("[LOG] remain cnt {} is less than 1, remains all logs files".format(remains_cnt))
        return
    need_to_delete, remains = _get_files_to_clean(remains_cnt)
    for f in need_to_delete:
        os.remove(f)
    logger.info("[LOG] clean {} logs files and remain {} log files".format(len(need_to_delete), len(remains)))


def _get_files_to_clean(remains_cnt):
    files = log_file_handler.getFilesToDelete()
    if len(files) <= remains_cnt:
        return [], files
    delete_cnt = len(files) - remains_cnt
    return files[:delete_cnt], files[delete_cnt:]
