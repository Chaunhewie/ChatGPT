from bridge.bot_chat import chat_factory
from bridge.bot_voice import voice_factory
from common import const
from conf.config import get_conf


class Bridge(object):
    def __init__(self):
        self.chat_gpt_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]
        self.open_ai_models = ["text-davinci-003"]

    def fetch_reply_content(self, query, context):
        return chat_factory.create_bot(self.parse_bot_type()).reply(query, context)

    def fetch_voice_to_text(self, voiceFile):
        return voice_factory.create_voice(self.parse_bot_type_v2t()).voiceToText(voiceFile)

    def fetch_text_to_voice(self, text):
        return voice_factory.create_voice(self.parse_bot_type_t2v()).textToVoice(text)

    def parse_bot_type(self):
        model_type = get_conf("model")
        if model_type in self.chat_gpt_models:
            return const.BotChatGPT
        elif model_type in self.open_ai_models:
            return const.BotOpenAI
        return const.BotChatGPT

    def parse_bot_type_v2t(self):
        return const.BotVoiceOpenAI

    def parse_bot_type_t2v(self):
        return const.BotVoiceBaidu
