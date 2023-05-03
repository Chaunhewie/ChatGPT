from abc import ABC

from flask import Flask, request

from channel.channel import Channel
from common.const import *
from conf.config import get_conf

app = Flask("ChatGPT")


@app.route('/')
def index():
    print('Hello, World!')


@app.route('/chatgpt', methods=['GET', 'POST'])
def chatgpt():
    print('Hello, World!')
    if request.method == 'GET':
        return 'Hello, World!'
    elif request.method == 'POST':
        data = request.get_data()
        return f'Received data: {data.decode()}'


class LarkChannel(Channel, ABC):
    def __init__(self):
        super().__init__(ChannelTypeLark)
        self.name = ChannelTypeLark
        self.host = get_conf('channel.lark.host', '127.0.0.1')
        self.port = get_conf('channel.lark.port', 10010)

    def startup(self):
        app.run(host=self.host, port=self.port)
