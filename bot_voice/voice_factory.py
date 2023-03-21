"""
bot_voice factory
"""
from common.const import BotVoiceBaidu, BotVoiceGoogle, BotVoiceOpenAI


def create_voice(voice_type):
    """
    create a bot_voice instance
    :param voice_type: bot_voice type code
    :return: bot_voice instance
    """
    if voice_type == BotVoiceBaidu:
        from bot_voice.baidu.baidu_voice import BaiduVoice
        return BaiduVoice()
    elif voice_type == BotVoiceGoogle:
        from bot_voice.google.google_voice import GoogleVoice
        return GoogleVoice()
    elif voice_type == BotVoiceOpenAI:
        from bot_voice.openai.openai_voice import OpenaiVoice
        return OpenaiVoice()
    raise RuntimeError
