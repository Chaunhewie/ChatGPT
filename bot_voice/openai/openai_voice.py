"""
google bot_voice service
"""
import openai

from bot_voice.voice import Voice
from common.const import BotVoiceOpenAI
from common.log import logger
from config import conf


class OpenaiVoice(Voice):
    def __init__(self):
        super().__init__(BotVoiceOpenAI)
        self.name = BotVoiceOpenAI
        openai.api_key = conf().get('open_ai_api_key')

    def voiceToText(self, voice_file):
        logger.debug(
            '[Openai] bot_voice file name={}'.format(voice_file))
        file = open(voice_file, "rb")
        reply = openai.Audio.transcribe("whisper-1", file)
        text = reply["text"]
        logger.info(
            '[Openai] voiceToText text={} bot_voice file name={}'.format(text, voice_file))
        return text

    def textToVoice(self, text):
        pass
