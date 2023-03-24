# encoding:utf-8
"""
google bot_voice service
"""

import os
import subprocess
import time

import pyttsx3
import speech_recognition

from bridge.bot_voice.voice import Voice
from common.const import BotVoiceGoogle
from common.tmp_dir import tmp_path


class GoogleVoice(Voice):
    recognizer = speech_recognition.Recognizer()
    engine = pyttsx3.init()

    def __init__(self):
        super().__init__(BotVoiceGoogle)
        self.name = BotVoiceGoogle
        # 语速
        self.engine.setProperty('rate', 200)
        # 音量
        self.engine.setProperty('volume', 1.0)
        self.engine.runAndWait()
        # 音色
        # voices = self.engine.getProperty('voices')
        # self.engine.setProperty('voice', voices[1].id)  # 0为男声，1为女声
        # self.engine.setProperty('voiceAge', 'Teen')  # 'Child'、'Teen'、'Adult' 和 'Senior'

    def voiceToText(self, voice_file):
        new_file = voice_file.replace('.mp3', '.wav')
        subprocess.call('ffmpeg -i ' + voice_file + ' -acodec pcm_s16le -ac 1 -ar 16000 ' + new_file, shell=True)
        with speech_recognition.AudioFile(new_file) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio, language='zh-CN')
            self.info('voiceToText text={} bot_voice file name={}'.format(text, voice_file))
            return text
        except speech_recognition.UnknownValueError:
            return "抱歉，我听不懂。"
        except speech_recognition.RequestError as e:
            return "抱歉，无法连接到 Google 语音识别服务；{0}".format(e)

    def textToVoice(self, text):
        self.debug('textToVoice get text={} and waiting to build voice'.format(text))
        textFile = os.path.join(tmp_path(), '语音回复_' + str(int(time.time_ns())) + '.wav')
        self.engine.save_to_file(text, textFile)
        # self.engine.say(text)
        self.engine.runAndWait()
        self.info('textToVoice text={} bot_voice file name={}'.format(text, textFile))
        return textFile

# print(GoogleVoice().textToVoice("你好！有什么问题需要我来回答或帮助解决吗？"))
# print(GoogleVoice().textToVoice("hello？"))
