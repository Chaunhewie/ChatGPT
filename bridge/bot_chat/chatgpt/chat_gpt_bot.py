# encoding:utf-8

import time

import openai

from bridge.bot_chat.chat import Chat
from common.const import BotChatGPT
from common.expired_dict import ExpiredDict
from config import conf

if conf().get('expires_in_seconds', 0) > 0:
    all_sessions = ExpiredDict(conf().get('expires_in_seconds'))
else:
    all_sessions = dict()


# OpenAI对话模型API (可用)
class ChatGPTBot(Chat):
    def __init__(self):
        super().__init__(BotChatGPT)
        self.name = BotChatGPT
        openai.api_key = conf().get('open_ai_api_key')
        if len(conf().get('open_ai_api_base')) > 0:
            openai.api_base = conf().get('open_ai_api_base')
        proxy = conf().get('proxy')
        if proxy:
            openai.proxy = proxy

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            self.info("query={}".format(query))
            session_id = context.get('session_id') or context.get('from_user_id')
            clear_memory_commands = conf().get('clear_memory_commands', ['#清除记忆'])
            if query in clear_memory_commands:
                Session.clear_session(session_id)
                answer = '记忆已清除'
                self.info("answer={}".format(answer))
                return answer
            elif query == '#清除所有':
                Session.clear_all_session()
                answer = '所有人记忆已清除'
                self.info("answer={}".format(answer))
                return answer

            session = Session.build_session_query(query, session_id)
            self.debug("session query={}".format(session))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, session_id, 0)
            self.debug(
                "new_query={}, session_id={}, reply_cont={}".format(session, session_id, reply_content["content"]))
            if reply_content["completion_tokens"] > 0:
                Session.save_session(reply_content["content"], session_id, reply_content["total_tokens"])
            self.info("answer={}".format(reply_content["content"]))
            return reply_content["content"]

        elif context.get('type', None) == 'IMAGE_CREATE':
            self.info("image_query={}".format(query))
            return self.create_img(query, 0)

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
                model=conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
                messages=session,
                temperature=conf().get('temperature', 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
                # max_tokens=4096,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=conf().get('frequency_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=conf().get('presence_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
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
                size="256x256"  # 图片大小,可选有 256x256, 512x512, 1024x1024
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


class Session(object):
    @staticmethod
    def build_session_query(query, session_id):
        """
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
        :param query: query content
        :param session_id: session id
        :return: query content with conversation
        """
        session = all_sessions.get(session_id, [])
        if len(session) == 0:
            system_prompt = conf().get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            all_sessions[session_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(answer, session_id, total_tokens):
        max_tokens = conf().get("conversation_max_tokens")
        if not max_tokens:
            # default 3000
            max_tokens = 1000
        max_tokens = int(max_tokens)

        session = all_sessions.get(session_id)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'content': answer}
            session.append(gpt_item)

        # discard exceed limit conversation
        Session.discard_exceed_conversation(session, max_tokens, total_tokens)

    @staticmethod
    def discard_exceed_conversation(session, max_tokens, total_tokens):
        dec_tokens = int(total_tokens)
        # logger.info("prompt tokens used={},max_tokens={}".format(used_tokens,max_tokens))
        while dec_tokens > max_tokens:
            # pop first conversation
            if len(session) > 3:
                session.pop(1)
                session.pop(1)
            else:
                break
            dec_tokens = dec_tokens - max_tokens

    @staticmethod
    def clear_session(session_id):
        all_sessions[session_id] = []

    @staticmethod
    def clear_all_session():
        all_sessions.clear()