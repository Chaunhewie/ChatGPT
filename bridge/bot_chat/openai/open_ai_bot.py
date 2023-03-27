# encoding:utf-8

import time

import openai

from bridge.bot_chat.chat import Chat
from bridge.bot_chat.session.session import UserSession
from common.const import *
from conf.config import get_conf


# OpenAI对话模型API (可用)
class OpenAIBot(Chat):
    def __init__(self):
        super().__init__(BotOpenAI)
        self.name = BotOpenAI
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

            from_user_id = context.get('from_user_id') or context.get('session_id')
            answer = UserSession.check_and_clear(query, from_user_id)
            if len(answer) > 0:
                self.info("answer={}".format(answer))
                return answer
            new_query = UserSession.build_session_query(query_type, query, from_user_id)
            self.debug("session query={}".format(new_query))

            reply_content = self.reply_text(new_query, from_user_id, 0)
            self.debug("user={}, reply_cont={}".format(from_user_id, reply_content))
            if reply_content and query:
                UserSession.save_session(query_type, query, reply_content, from_user_id)

            self.info("answer={}".format(reply_content))
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, query, user_id, retry_count=0):
        try:
            response = openai.Completion.create(
                model=get_conf("model", default="text-davinci-003"),  # 对话模型的名称
                prompt=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                # max_tokens=1200,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.5,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.5,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["\n\n\n"]
            )
            res_content = response.choices[0]['text'].strip().replace('<|endoftext|>', '')
            self.info("reply={}".format(res_content))
            return res_content
        except openai.error.RateLimitError as e:
            # rate limit exception
            if retry_count < 1:
                time.sleep(5)
                self.warn("RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.reply_text(query, user_id, retry_count + 1)
            else:
                self.warn("RateLimit exceed: {}".format(e))
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            # unknown exception
            self.error(e)
            # Session.clear_session(user_id)
            return "请再问我一次吧"

    def create_img(self, query, retry_count=0):
        try:
            self.info("image_query={}".format(query))
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
                return self.reply_text(query, retry_count + 1)
            else:
                self.warn("ImgCreate RateLimit exceed: {}".format(e))
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            self.error(e)
            return None
