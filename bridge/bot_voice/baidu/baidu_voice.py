"""
baidu bot_voice service
"""

import time

from aip import AipSpeech

from bridge.bot_voice.voice import Voice
from common.const import BotVoiceBaidu
from common.tmp_dir import TmpDir
from conf.config import get_conf


class BaiduVoice(Voice):
    APP_ID = get_conf('bot.baidu_voice.app_id')
    API_KEY = get_conf('bot.baidu_voice.api_key')
    SECRET_KEY = get_conf('bot.baidu_voice.secret_key')
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    def __init__(self):
        super().__init__(BotVoiceBaidu)
        self.name = BotVoiceBaidu

    def voiceToText(self, voice_file):
        pass

    def textToVoice(self, text):
        self.info('textToVoice text={}'.format(text))
        result = self.client.synthesis(text, 'zh', 1, {'spd': 5, 'pit': 5, 'vol': 5, 'per': 111})
        if not isinstance(result, dict):
            fileName = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
            with open(fileName, 'wb') as f:
                f.write(result)
            self.info('bot_voice file name={}'.format(fileName))
            return fileName
        else:
            self.error('textToVoice error={}'.format(result))
            return None
