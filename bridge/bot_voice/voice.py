"""
Voice service abstract class
"""

from common.log import logger


class Voice(object):
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

    def voiceToText(self, voice_file):
        """
        Send bot_voice to bot_voice service and get text
        """
        raise NotImplementedError

    def textToVoice(self, text):
        """
        Send text to bot_voice service and get bot_voice
        """
        raise NotImplementedError
