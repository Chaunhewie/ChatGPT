# encoding:utf-8


from common.expired_dict import ExpiredDict
from common.log import logger
from conf.config import get_conf

expire = get_conf('bot.open_ai.expire_sec', default=0)
if expire > 0:
    all_sessions = ExpiredDict(expire)
    user_session = ExpiredDict(expire)
else:
    all_sessions = dict()
    user_session = dict()


class Session(object):
    @staticmethod
    def check_and_clear(query, session_id):
        if query in get_conf('clear_all_memory_commands', default=['#清除所有']):
            Session.clear_all_session()
            answer = '所有记忆已清除'
            logger.info("[Session] clear all sessions success")
            return answer
        if query in get_conf('clear_memory_commands', default=['#清除记忆']):
            Session.clear_session(session_id)
            answer = '记忆已清除'
            logger.info("[Session] clear session for {} success".format(session_id))
            return answer
        return ""

    @staticmethod
    def build_session_query(query_type, query, session_id):
        """
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
        :param query_type: query type (TEXT, CODE, IMAGE_CREATE, etc)
        :param query: query content
        :param session_id: session id
        :return: query content with conversation
        """
        session = all_sessions.get(session_id, [])
        if len(session) == 0:
            some_prompt = get_conf("some_prompt")
            if query in some_prompt:
                for prompt in some_prompt[query]:
                    system_item = {'role': 'system', 'content': prompt}
                    session.append(system_item)
                all_sessions[session_id] = session
                return Session._filtered_session(session)
            else:
                system_prompt = get_conf("character_desc")
                system_item = {'role': 'system', 'content': system_prompt}
                session.append(system_item)
                all_sessions[session_id] = session
        user_item = {'role': 'user', 'type': query_type, 'content': query}
        session.append(user_item)
        return Session._filtered_session(session, query_type)

    @staticmethod
    def _filtered_session(session, query_type):
        _session = []
        for s in session:
            if s.get('type', query_type) == query_type:
                _s = {'role': s['role'], 'content': s['content']}
                _session.append(_s)
        return _session

    @staticmethod
    def save_session(query_type, answer, session_id, total_tokens):
        max_tokens = get_conf("bot.open_ai.max_tokens")
        if not max_tokens:
            # default 1000
            max_tokens = 1000
        max_tokens = int(max_tokens)

        session = all_sessions.get(session_id)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'type': query_type, 'content': answer}
            session.append(gpt_item)

        # discard exceed limit conversation
        Session.discard_exceed_conversation(session, max_tokens, total_tokens)

    @staticmethod
    def discard_exceed_conversation(session, max_tokens, total_tokens):
        dec_tokens = int(total_tokens)
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


class UserSession(object):
    @staticmethod
    def check_and_clear(query, user_id):
        if query in get_conf('clear_all_memory_commands', default=['#清除所有']):
            UserSession.clear_all_session()
            answer = '所有记忆已清除'
            return answer
        if query in get_conf('clear_memory_commands', default=['#清除记忆']):
            UserSession.clear_session(user_id)
            answer = '记忆已清除'
            return answer
        return ""

    @staticmethod
    def build_session_query(query_type, query, user_id):
        """
        build query with conversation history
        e.g.  Q: xxx
              A: xxx
              Q: xxx
        :param query_type: query type (TEXT, CODE, IMAGE_CREATE, etc)
        :param query: query content
        :param user_id: from user id
        :return: query content with conversaction
        """
        prompt = get_conf("character_desc")
        if prompt:
            prompt += "<|endoftext|>\n\n\n"
        session = user_session.get(user_id, None)
        if session:
            for conversation in session:
                prompt += "Q: " + conversation["question"] + "\n\n\nA: " + conversation["answer"] + "<|endoftext|>\n"
            prompt += "Q: " + query + "\nA: "
            return prompt
        else:
            return prompt + "Q: " + query + "\nA: "

    @staticmethod
    def save_session(query_type, query, answer, user_id):
        max_tokens = get_conf("bot.open_ai.max_tokens")
        if not max_tokens:
            # default 1000
            max_tokens = 1000
        conversation = dict()
        conversation["question"] = query
        conversation["answer"] = answer
        session = user_session.get(user_id)
        if session:
            # append conversation
            session.append(conversation)
        else:
            # create session
            queue = list()
            queue.append(conversation)
            user_session[user_id] = queue

        # discard exceed limit conversation
        UserSession.discard_exceed_conversation(user_session[user_id], max_tokens)

    @staticmethod
    def discard_exceed_conversation(session, max_tokens):
        count = 0
        count_list = list()
        for i in range(len(session) - 1, -1, -1):
            # count tokens of conversation list
            history_conv = session[i]
            count += len(history_conv["question"]) + len(history_conv["answer"])
            count_list.append(count)

        for c in count_list:
            if c > max_tokens:
                # pop first conversation
                session.pop(0)

    @staticmethod
    def clear_session(user_id):
        user_session[user_id] = []

    @staticmethod
    def clear_all_session():
        user_session.clear()
