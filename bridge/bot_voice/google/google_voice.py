"""
google bot_voice service
"""

import subprocess
import time

import pyttsx3
import speech_recognition

from bridge.bot_voice.voice import Voice
from common.const import BotVoiceGoogle
from common.tmp_dir import TmpDir


class GoogleVoice(Voice):
    recognizer = speech_recognition.Recognizer()
    engine = pyttsx3.init()

    def __init__(self):
        super().__init__(BotVoiceGoogle)
        self.name = BotVoiceGoogle
        # 语速
        self.engine.setProperty('rate', 125)
        # 音量
        self.engine.setProperty('volume', 1.0)
        # 0为男声，1为女声
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('bot_voice', voices[1].id)

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
        textFile = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
        self.engine.save_to_file(text, textFile)
        self.engine.runAndWait()
        self.info('textToVoice text={} bot_voice file name={}'.format(text, textFile))
        return textFile
