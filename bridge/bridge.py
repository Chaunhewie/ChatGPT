from bridge.bot_chat import chat_factory
from bridge.bot_voice import voice_factory
from common import const
from conf.config import get_conf


class Bridge(object):
    def __init__(self):
        self.chat_gpt_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]
        self.open_ai_models = ["text-davinci-003"]
        self.open_ai_v2t_models = ["whisper-1"]
        self.open_ai_t2v_models = []

    def fetch_reply_content(self, query, context):
        return chat_factory.create_bot(self.parse_bot_type()).reply(query, context)

    def fetch_voice_to_text(self, voiceFile):
        return voice_factory.create_voice(self.parse_bot_type_v2t()).voice_to_text(voiceFile)

    def fetch_text_to_voice(self, text):
        return voice_factory.create_voice(self.parse_bot_type_t2v()).text_to_voice(text)

    def parse_bot_type(self):
        model_type = get_conf("model")
        if model_type in self.chat_gpt_models:
            return const.BotChatGPT
        elif model_type in self.open_ai_models:
            return const.BotOpenAI
        return const.BotChatGPT

    def parse_bot_type_v2t(self):
        model_type = get_conf("model_v2t")
        if model_type in self.open_ai_v2t_models:
            return const.BotVoiceOpenAI
        return const.BotVoiceGoogle

    def parse_bot_type_t2v(self):
        model_type = get_conf("model_t2v")
        if model_type in self.open_ai_t2v_models:
            return const.BotVoiceOpenAI
        return const.BotVoiceGoogle
