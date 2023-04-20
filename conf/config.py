# encoding:utf-8

import json
import os

from common.log import logger

config = {}


def load_config():
    global config
    config_path = "./conf/config.json"
    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据conf/config_tmpl.json模板创建conf/config.json文件')
    with open(config_path, mode='r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("[CONF] load config: {}".format(config))


def get_conf(path: str, default=None):
    path_list = path.split(".")
    c = config
    for p in path_list:
        if p not in c:
            return default
        c = c[p]
    return c
