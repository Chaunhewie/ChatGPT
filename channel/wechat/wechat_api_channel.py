from abc import ABC

from channel.channel import Channel
from common.const import ChannelTypeWXAPI


class WechatChannel(Channel, ABC):
    def __init__(self):
        super().__init__(ChannelTypeWXAPI)
        self.name = ChannelTypeWXAPI
        pass
