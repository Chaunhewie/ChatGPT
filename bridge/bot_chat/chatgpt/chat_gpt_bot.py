# encoding:utf-8

import time

import openai

from bridge.bot_chat.chat import Chat
from bridge.bot_chat.session.session import Session
from common.const import *
from conf.config import get_conf


# OpenAI对话模型API (可用)
class ChatGPTBot(Chat):
    def __init__(self):
        super().__init__(BotChatGPT)
        self.name = BotChatGPT
        openai.api_key = get_conf('bot.open_ai.api_key')
        api_base = get_conf('bot.open_ai.api_base', default="")
        if len(api_base) > 0:
            openai.api_base = api_base
        proxy = get_conf('bot.open_ai.proxy', default="")
        if len(proxy) > 0:
            openai.proxy = proxy

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == ContextTypeText:
            self.info("query={}".format(query))
            query_type = ContextTypeText

            session_id = context.get('session_id') or context.get('from_user_id')
            answer = Session.check_and_clear(query, session_id)
            if len(answer) > 0:
                self.info("answer={}".format(answer))
                return answer
            session = Session.build_session_query(query_type, query, session_id)
            self.debug("session query={}".format(session))

            reply_content = self.reply_text(session, session_id, 0)
            self.debug("session_id={}, reply_cont={}".format(session_id, reply_content["content"]))
            if reply_content["completion_tokens"] > 0:
                Session.save_session(query_type, reply_content["content"], session_id, reply_content["total_tokens"])
            self.info("answer={}".format(reply_content["content"]))
            return reply_content["content"]

        elif context.get('type') == ContextTypeImageCreate:
            self.info("image_query={}".format(query))
            return self.create_img(query, 0)

        elif context.get('type') == ContextTypeCode:
            self.info("code_query={}".format(query))
            return ""  # todo

    def reply_text(self, session, session_id, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            response = openai.ChatCompletion.create(
                model=get_conf("model", default="gpt-3.5-turbo"),  # 对话模型的名称
                messages=session,
                temperature=0.2,  # 值在[0,1]之间，越大表示回复越具有不确定性
                # max_tokens=4096,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.5,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.5,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            )
            self.debug("reply={}, total_tokens={}".format(response.choices[0]['message']['content'],
                                                          response["usage"]["total_tokens"]))
            return {"total_tokens": response["usage"]["total_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "content": response.choices[0]['message']['content']}
        except openai.error.RateLimitError as e:
            # rate limit exception
            if retry_count < 1:
                time.sleep(5)
                self.warn("RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, session_id, retry_count + 1)
            else:
                self.warn("RateLimit exceed: {}".format(e))
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧~"}
        except openai.error.APIConnectionError as e:
            self.warn("APIConnection failed: {}".format(e))
            return {"completion_tokens": 0, "content": "我连接不到网络啦，请稍后再试试~"}
        except openai.error.Timeout as e:
            self.warn("Timeout: {}".format(e))
            return {"completion_tokens": 0, "content": "我请求超时啦，请稍后再试试~"}
        except Exception as e:  # unknown exception
            self.error("unknown err: {}".format(e))
            # Session.clear_session(session_id)
            return {"completion_tokens": 0, "content": "请再问我一次吧"}

    def create_img(self, query, retry_count=0):
        try:
            response = openai.Image.create(
                prompt=query,  # 图片描述
                n=1,  # 每次生成图片的数量
                size="512x512"  # 图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            self.info("image_url={}".format(image_url))
            return image_url
        except openai.error.RateLimitError as e:
            if retry_count < 1:
                time.sleep(5)
                self.warn("ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.create_img(query, retry_count + 1)
            else:
                self.warn("ImgCreate RateLimit exceed: {}".format(e))
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            self.error("unknown err: {}".format(e))
            return None
