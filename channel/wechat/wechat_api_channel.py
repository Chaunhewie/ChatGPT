from abc import ABC

from channel.channel import Channel
from common.const import ChannelTypeWXAPI


class WechatAPIChannel(Channel, ABC):
    def __init__(self):
        super().__init__(ChannelTypeWXAPI)
        self.name = ChannelTypeWXAPI
        pass

    def startup(self):
        pass
