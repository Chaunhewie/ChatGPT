# encoding:utf-8
"""
baidu bot_voice service
"""

import os
import time

from aip import AipSpeech

from bridge.bot_voice.voice import Voice
from common.const import BotVoiceBaidu
from common.tmp_dir import tmp_path
from conf.config import get_conf


class BaiduVoice(Voice):
    def __init__(self):
        super().__init__(BotVoiceBaidu)
        self.name = BotVoiceBaidu
        self.client = AipSpeech(get_conf('bot.baidu_voice.app_id'), get_conf('bot.baidu_voice.api_key'), get_conf('bot.baidu_voice.secret_key'))

    def voice_to_text(self, voice_file):
        self.info('voice_to_text not implemented')
        pass

    def text_to_voice(self, text):
        self.info('textToVoice text={}'.format(text))
        result = self.client.synthesis(text, 'zh', 1, {'spd': 5, 'pit': 5, 'vol': 5, 'per': 111})
        if not isinstance(result, dict):
            file_name = os.path.join(tmp_path() + '语音回复_', str(int(time.time_ns())) + '.mp3')
            with open(file_name, 'wb') as f:
                f.write(result)
            self.info('bot_voice file name={}'.format(file_name))
            return file_name
        else:
            self.error('textToVoice error={}'.format(result))
            return None
