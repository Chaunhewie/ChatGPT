"""
Message sending channel abstract class
"""

from bridge.bridge import Bridge
from common.log import logger, clean_log
from common.tmp_dir import clean_tmp
from conf.config import get_conf, load_config


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

    @staticmethod
    def build_reply_content(query, context=None):
        logger.debug("[Channel] query={}".format(query))
        if query == "#prompt":
            some_prompt = get_conf('some_prompt', default=["目前没有相关提示项"])
            answer = "\n请先清除上下文记忆后直接输入对应角色来启用此功能，当前支持设定的角色如下：\n" + ",".join(some_prompt.keys())
            return answer
        if query in get_conf('update_config_commands', default=['#更新配置']):
            load_config()
            answer = '配置已更新'
            return answer
        if query in get_conf('clear_tmp_commands', default=['#清除音频']):
            clean_tmp()
            answer = '音频已清除'
            return answer
        if query in get_conf('clear_logs_commands', default=['#清除日志']):
            clean_log(int(get_conf("clear_logs_remains_cnt", 3)))
            answer = '日志已清除'
            return answer
        if query in get_conf('clear_all_memory_commands', default=['#清除所有']):
            clean_log(int(get_conf("clear_logs_remains_cnt", 3)))
            clean_tmp()
        return Bridge().fetch_reply_content(query, context)

    @staticmethod
    def build_voice_to_text(voice_file):
        return Bridge().fetch_voice_to_text(voice_file)

    @staticmethod
    def build_text_to_voice(text):
        return Bridge().fetch_text_to_voice(text)
