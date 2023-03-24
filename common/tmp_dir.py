import os
import pathlib
import shutil

from common.log import logger

tmpFilePath = pathlib.Path('./tmp')

pathExists = os.path.exists(tmpFilePath)
if not pathExists:
    os.makedirs(tmpFilePath)


def tmp_path():
    return tmpFilePath


def clean_tmp():
    path = tmp_path()
    if os.path.exists(path):
        shutil.rmtree(path)
        os.mkdir(path)
        logger.info("[TMP] clean tmp files success")
