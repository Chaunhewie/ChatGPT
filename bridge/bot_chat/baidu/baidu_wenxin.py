# encoding:utf-8

import wenxin_api
from wenxin_api.tasks.free_qa import FreeQA

from bridge.bot_chat.chat import Chat
from common.const import BotBaiduWX
from conf.config import get_conf


# Baidu 文心一言对话接口: https://wenxin.baidu.com/wenxin/docs#2l6tgx5rc
class BaiduWenXin(Chat):
    def __init__(self):
        super().__init__(BotBaiduWX)
        self.name = BotBaiduWX
        wenxin_api.ak = get_conf("bot.baidu.ak")
        wenxin_api.sk = get_conf("bot.baidu.sk")
        # 参数描述：https://wenxin.baidu.com/wenxin/docs#dl6tgxw5f
        self.default_post_data = {
            "text": "问题：文心一言，你好！\n回答：",
            # "seq_len": 4096,
            "topp": 0.5,
            "penalty_score": 1.2,
            "min_dec_len": 2,
            "min_dec_penalty_text": "。？：！[<S>]",
            "is_unidirectional": 1,
            "task_prompt": "Misc",
            "mask_type": "paragraph"
        }

    def reply(self, query, context=None):
        self.info("query={}".format(query))
        post_data = self.default_post_data.copy()
        post_data['text'] = query
        self.debug("post_date={}".format(post_data))

        response = FreeQA.create(**post_data)
        if response:
            answer = response.json()['result']['context']['SYS_PRESUMED_HIST'][1]
            self.info("answer={}".format(answer))
            return answer
        raise RuntimeError("baidu wenxin post failed")
