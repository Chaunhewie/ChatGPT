# encoding:utf-8
"""
google bot_voice service
"""

import os
import subprocess
import time

import gtts
import pyttsx3
import speech_recognition

from bridge.bot_voice.voice import Voice
from common.const import BotVoiceGoogle
from common.tmp_dir import tmp_path
from conf.config import get_conf


class GoogleVoice(Voice):
    def __init__(self):
        super().__init__(BotVoiceGoogle)
        self.name = BotVoiceGoogle

        self.recognizer = speech_recognition.Recognizer()
        self.engine = pyttsx3.init()
        # 语速
        self.engine.setProperty('rate', 250)
        # 音量
        self.engine.setProperty('volume', 1.0)
        self.engine.runAndWait()
        # 音色
        # voices = self.engine.getProperty('voices')
        # self.engine.setProperty('voice', voices[0].id)  # 0为男声，1为女声
        # self.engine.setProperty('voiceAge', 'Teen')  # 'Child'、'Teen'、'Adult' 和 'Senior'

    def voice_to_text(self, voice_file):
        self.info('bot_voice file name={}'.format(voice_file))
        with speech_recognition.AudioFile(self._trans_wav_file(voice_file)) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio, language='zh-CN')
            self.info('voiceToText text={} bot_voice file name={}'.format(text, voice_file))
            return text
        except speech_recognition.UnknownValueError:
            return "抱歉，我听不懂。"
        except speech_recognition.RequestError as e:
            return "抱歉，无法连接到 Google 语音识别服务；{0}".format(e)

    def _trans_wav_file(self, voice_file: str):
        if voice_file.endswith(".wav"):
            return voice_file
        new_file = ".".join(voice_file.split(".")[:-1]) + '.wav'
        self.info("_trans_wav_file {} as {}".format(voice_file, new_file))
        subprocess.call('ffmpeg -i ' + voice_file + ' -acodec pcm_s16le -ac 1 -ar 16000 ' + new_file, shell=True)
        return new_file

    def text_to_voice(self, text):
        if get_conf("bot.google_voice.t2v_using_online_api", False):
            return self._text_to_voice_online(text)
        return self._text_to_voice_offline(text)

    def _text_to_voice_offline(self, text):
        self.debug('_text_to_voice_offline get text={} and waiting to build voice'.format(text))
        text_file = os.path.join(tmp_path(), '语音回复_' + str(int(time.time_ns())) + '.wav')
        self.engine.save_to_file(text, text_file)
        # self.engine.say(text)
        self.engine.runAndWait()
        self.info('_text_to_voice_offline text={} bot_voice file name={}'.format(text, text_file))
        return text_file

    def _text_to_voice_online(self, text):
        self.debug('_text_to_voice_online get text={} and waiting to build voice'.format(text))
        text_file = os.path.join(tmp_path(), '语音回复_' + str(int(time.time_ns())) + '.wav')
        tts = gtts.gTTS(text, lang="zh-cn")
        tts.save(text_file)
        self.info('_text_to_voice_online text={} bot_voice file name={}'.format(text, text_file))
        return text_file

# with open('books/tmp.txt', 'r') as f:
#     text = f.read()
# GoogleVoice()._text_to_voice_offline(text)
