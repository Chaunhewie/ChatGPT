"""
Message sending channel abstract class
"""

from bridge.bridge import Bridge
from common.log import logger
from config import load_config


class Channel(object):
    def __init__(self, name: str):
        self.name = name

    def debug(self, msg):
        logger.debug("[{}] {}".format(self.name, msg), stacklevel=2)

    def info(self, msg):
        logger.info("[{}] {}".format(self.name, msg), stacklevel=2)

    def warn(self, msg):
        logger.warn("[{}] {}".format(self.name, msg), stacklevel=2)

    def error(self, msg):
        logger.error("[{}] {}".format(self.name, msg), stacklevel=2)

    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    def send(self, msg, receiver):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return: 
        """
        raise NotImplementedError

    @staticmethod
    def build_reply_content(query, context=None):
        if query == '#更新配置':
            load_config()
            answer = '配置已更新'
            return answer
        return Bridge().fetch_reply_content(query, context)

    @staticmethod
    def build_voice_to_text(voice_file):
        return Bridge().fetch_voice_to_text(voice_file)

    @staticmethod
    def build_text_to_voice(text):
        return Bridge().fetch_text_to_voice(text)
