# encoding:utf-8

import json
import os

from common.log import logger

config = {}


def load_config():
    global config
    config_path = "config.json"
    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据config-template.json模板创建config.json文件')
    with open(config_path, mode='r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("[INIT] load config: {}".format(config))


def conf():
    return config
