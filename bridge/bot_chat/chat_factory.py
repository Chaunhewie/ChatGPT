"""
channel factory
"""
from common import const


def create_bot(bot_type):
    """
    create a channel instance
    :param bot_type:
    :return: channel instance
    """
    if bot_type == const.BotBaiduUnit:
        # Baidu Unit对话接口
        from bridge.bot_chat.baidu.baidu_unit_bot import BaiduUnitBot
        return BaiduUnitBot()
    elif bot_type == const.BotChatGPT:
        # ChatGPT 网页端web接口
        from bridge.bot_chat.chatgpt.chat_gpt_bot import ChatGPTBot
        return ChatGPTBot()
    elif bot_type == const.BotOpenAI:
        # OpenAI 官方对话模型API
        from bridge.bot_chat.openai.open_ai_bot import OpenAIBot
        return OpenAIBot()
    raise RuntimeError
