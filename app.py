# encoding:utf-8

from channel import channel_factory
from common.log import logger
from conf import config

if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        # create channel
        channel = channel_factory.create_channel(config.get_conf("channel"))

        # startup channel
        channel.startup()
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)
