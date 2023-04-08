"""
google bot_voice service
"""
import openai

from bridge.bot_voice.voice import Voice
from common.const import BotVoiceOpenAI
from conf.config import get_conf


class OpenaiVoice(Voice):
    def __init__(self):
        super().__init__(BotVoiceOpenAI)
        self.name = BotVoiceOpenAI
        openai.api_key = get_conf('bot.open_ai.api_key')

    def voice_to_text(self, voice_file):
        self.info('bot_voice file name={}'.format(voice_file))
        file = open(voice_file, "rb")
        reply = openai.Audio.transcribe(get_conf("model_v2t", "whisper-1"), file)
        text = reply["text"]
        self.info('voiceToText text={} bot_voice file name={}'.format(text, voice_file))
        return text

    def text_to_voice(self, text):
        self.info('text_to_voice not implemented')
        pass
