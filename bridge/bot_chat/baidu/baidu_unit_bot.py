# encoding:utf-8
import json

import requests

from bridge.bot_chat.chat import Chat
from common.const import BotBaiduUnit
from conf.config import get_conf


# Baidu Unit对话接口 (可用, 但能力较弱)
class BaiduUnitBot(Chat):
    def __init__(self):
        super().__init__(BotBaiduUnit)
        self.name = BotBaiduUnit
        self.access_key = get_conf("bot.baidu.ak")
        self.secret_key = get_conf("bot.baidu.sk")
        self.get_token_url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + self.access_key + '&client_secret=' + self.secret_key
        self.post_url = 'https://aip.baidubce.com/rpc/2.0/unit/service/v3/chat?access_token='
        self.post_headers = {'content-type': 'application/x-www-form-urlencoded'}
        self.default_post_data = {
            "version": "3.0",
            "service_id": "S73177",
            "session_id": "",
            "log_id": "7758521",
            "skill_ids": ["1221886"],
            "request": {
                "terminal_id": "88888",
                "query": "",
                "hyper_params": {
                    "chat_custom_bot_profile": 1
                }
            }
        }

    def reply(self, query, context=None):
        self.info("query={}".format(query))
        post_data = self.default_post_data.copy()
        post_data['request']['query'] = query
        post_data_str = json.dumps(post_data)
        self.debug("post_date={}".format(post_data))

        response = requests.post(self.post_url + self.get_token(), data=post_data_str.encode(),
                                 headers=self.post_headers)
        if response:
            answer = response.json()['result']['context']['SYS_PRESUMED_HIST'][1]
            self.info("answer={}".format(answer))
            return answer
        raise RuntimeError("baidu bot_chat post failed")

    def get_token(self):
        response = requests.get(self.get_token_url)
        if response:
            self.debug("get_token resp={}".format(response.json()))
            return response.json()['access_token']
        raise RuntimeError("baidu bot_chat token fetch failed.")
