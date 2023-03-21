"""
Auto-replay chat robot abstract class
"""
from common.log import logger


class Chat(object):
    def __init__(self, name: str):
        self.name = name

    def debug(self, msg):
        logger.debug("[{}] {}".format(self.name, msg))

    def info(self, msg):
        logger.info("[{}] {}".format(self.name, msg))

    def warn(self, msg):
        logger.warn("[{}] {}".format(self.name, msg))

    def error(self, msg):
        logger.error("[{}] {}".format(self.name, msg))

    def reply(self, query, context=None):
        """
        bot_chat auto-reply content
        :param query: received message
        :param context:
        :return: reply content
        """
        raise NotImplementedError
