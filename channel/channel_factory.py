"""
channel factory
"""
from common.const import ChannelTypeWX, ChannelTypeWXY, ChannelTypeWXAPI, ChannelTypeTerminal


def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == ChannelTypeWX:
        from channel.wechat.wechat_channel import WechatChannel
        return WechatChannel()
    elif channel_type == ChannelTypeWXY:
        from channel.wechat.wechaty_channel import WechatyChannel
        return WechatyChannel()
    elif channel_type == ChannelTypeWXAPI:
        from channel.wechat.wechat_api_channel import WechatAPIChannel
        return WechatAPIChannel()
    elif channel_type == ChannelTypeTerminal:
        from channel.terminal.terminal_channel import TerminalChannel
        return TerminalChannel()
    raise RuntimeError("unknown channel type:" + channel_type)
