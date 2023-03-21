"""
baidu bot_voice service
"""

import time

from aip import AipSpeech

from bot_voice.voice import Voice
from common.const import BotVoiceBaidu
from common.tmp_dir import TmpDir
from config import conf


class BaiduVoice(Voice):
    APP_ID = conf().get('baidu_app_id')
    API_KEY = conf().get('baidu_api_key')
    SECRET_KEY = conf().get('baidu_secret_key')
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    def __init__(self):
        super().__init__(BotVoiceBaidu)
        self.name = BotVoiceBaidu

    def voiceToText(self, voice_file):
        pass

    def textToVoice(self, text):
        result = self.client.synthesis(text, 'zh', 1, {
            'spd': 5, 'pit': 5, 'vol': 5, 'per': 111
        })
        if not isinstance(result, dict):
            fileName = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
            with open(fileName, 'wb') as f:
                f.write(result)
            self.info('textToVoice text={} bot_voice file name={}'.format(text, fileName))
            return fileName
        else:
            self.error('textToVoice error={}'.format(result))
            return None
