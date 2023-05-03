# encoding:utf-8

"""
wechat channel
"""
import io
import os
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

import itchat
import requests
from itchat.content import *

from channel.channel import Channel
from common.const import *
from common.tmp_dir import tmp_path
from common.utils import parse_prefix
from conf.config import get_conf

thread_pool = ThreadPoolExecutor(max_workers=8)


@itchat.msg_register(TEXT)
def handler_single_msg(msg):
    WechatChannel().handle_single_msg(msg)
    return None


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_group_msg(msg):
    WechatChannel().handle_group_msg(msg)
    return None


@itchat.msg_register(VOICE)
def handler_single_voice(msg):
    WechatChannel().handle_voice(msg)
    return None


@itchat.msg_register(VOICE, isGroupChat=True)
def handler_group_voice(msg):
    WechatChannel().handle_group_voice(msg)
    return None


class WechatChannel(Channel, ABC):
    def __init__(self):
        super().__init__(ChannelTypeWX)
        self.name = ChannelTypeWX
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login(enableCmdQR=2, hotReload=get_conf('channel.wechat.hot_reload', default=False))

        # start message listener
        itchat.run()

    def send(self, msg, receiver):
        itchat.send(msg, toUserName=receiver)
        self.debug('sendMsg={}, receiver={}'.format(msg, receiver))

    def send_file(self, file, receiver):
        itchat.send_file(file, toUserName=receiver)
        self.debug('sendFile={}, receiver={}'.format(file, receiver))

    def send_img(self, image_storage, receiver):
        itchat.send_image(image_storage, receiver)
        self.debug('sendImage, receiver={}'.format(receiver))

    def handle_voice(self, msg):
        if not get_conf('single_speech_recognition'):
            return
        self.debug("receive single voice msg: " + msg['FileName'])
        thread_pool.submit(self._do_handle_voice, msg)

    def _do_handle_voice(self, msg):
        from_user_id = msg['FromUserName']  # 发送人id
        to_user_id = msg['ToUserName']  # 接收人id
        other_user_id = msg['User'].get('UserName', "")  # 聊天对方的id
        other_user_nick = msg['User'].get('NickName', "")  # 聊天对方名称
        other_user_remark = msg['User'].get('RemarkName', "")  # 聊天对方备注
        other_user = other_user_id if len(other_user_id) > 0 else from_user_id
        if len(other_user_nick) > 0:
            other_user = other_user_nick
        if len(other_user_remark) > 0:
            other_user = other_user_remark

        # from_user_id == other_user_id 好友向自己发送消息
        # to_user_id == other_user_id 自己给好友发送消息
        self.info("[_do_handle_voice] other user is {}, from user {} -> to user {}".format(other_user, from_user_id, to_user_id))

        if len(other_user_id) <= 0:
            self.info("[_do_handle_voice] blank other user id and return fast")
            return ""

        # 下载音频并处理为文字
        file_name = os.path.join(tmp_path(), msg['FileName'])
        msg.download(file_name)
        query = super().build_voice_to_text(file_name)

        if get_conf('voice_reply_voice'):
            thread_pool.submit(self._do_send_voice, query, other_user_id)
        else:
            thread_pool.submit(self._do_send_text, query, other_user_id)

    def handle_group_voice(self, msg):
        if not get_conf('group_speech_recognition'):
            return
        self.debug("receive group voice msg: " + msg['FileName'])
        thread_pool.submit(self._do_handle_group_voice, msg)

    def _do_handle_group_voice(self, msg):
        group_name = msg['User'].get('NickName', "")
        group_id = msg['User'].get('UserName', "")
        self.info("[_do_handle_group_voice] group_name={}, group_id={}".format(group_name, group_id))
        if len(group_name) <= 0:
            self.info("[_do_handle_group_voice] blank group name and return fast")
            return ""

        config = get_conf("chat.group.{}".format(group_name), default=get_conf("chat.group.*", default=None))
        if config is None:
            self.info("[_do_handle_group_voice] group name={} not in group list and ignore".format(group_name))
            return
        if not config.get("handle_voice", False):
            self.info("[_do_handle_group_voice] group name={} not handle_voice and return".format(group_name))
            return

        file_name = os.path.join(tmp_path(), msg['FileName'])
        msg.download(file_name)
        query = super().build_voice_to_text(file_name)
        if get_conf('voice_reply_voice'):
            thread_pool.submit(self._do_send_voice, query, group_id)
        else:
            thread_pool.submit(self._do_send_group, query, msg)

    def handle_single_msg(self, msg):
        content = msg['Content']
        self.debug("receive single text content: {}".format(content))
        self._do_handle_single_msg(msg, content)

    def _do_handle_single_msg(self, msg, content):
        if "- - - - - - - - - - - - - - -" in content:
            self.debug("reference query skipped")
            return
        from_user_id = msg['FromUserName']  # 发送人id
        to_user_id = msg['ToUserName']  # 接收人id
        other_user_id = msg['User'].get('UserName', "")  # 聊天对方的id
        other_user_nick = msg['User'].get('NickName', "")  # 聊天对方名称
        other_user_remark = msg['User'].get('RemarkName', "")  # 聊天对方备注
        other_user = other_user_id if len(other_user_id) > 0 else from_user_id
        if len(other_user_nick) > 0:
            other_user = other_user_nick
        if len(other_user_remark) > 0:
            other_user = other_user_remark

        # from_user_id == other_user_id 好友向自己发送消息
        # to_user_id == other_user_id 自己给好友发送消息
        self.info("[_do_handle_single_msg] other user is {}, from user {} -> to user {}".format(other_user, from_user_id, to_user_id))

        if len(other_user_id) <= 0:
            self.info("[_do_handle_single_msg] blank other user id and return fast")
            return ""

        prefixs = get_conf('chat.single.prefix', default=[])
        except_prefixs = get_conf('chat.single.except_prefix', default=[])
        image_prefixs = get_conf('chat.image.prefix', default=[])
        prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix, content = parse_prefix(content, prefixs, except_prefixs, image_prefixs)
        self.debug("[_do_handle_single_msg] prefix={}, match_prefix={}, except_prefix={}, match_except_prefix={}, image_prefix={}, \
match_image_prefix={}".format(prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix))

        if not match_prefix:
            self.info("[_do_handle_single_msg] not match prefix and return fast")
            return

        if match_image_prefix:
            thread_pool.submit(self._do_send_img, content, other_user_id)
        else:
            thread_pool.submit(self._do_send_text, content, other_user_id)

    def handle_group_msg(self, msg):
        content = msg['Content']

        # content_list = content.split(' ', 1)
        # context_special_list = content.split('\u2005', 1)
        # if len(context_special_list) == 2:
        #     content = context_special_list[1]
        # elif len(content_list) == 2:
        #     content = content_list[1]

        self.debug("receive group text content: {}".format(content))
        self._do_handle_group_msg(msg, content)

    def _do_handle_group_msg(self, msg, content):
        if "- - - - - - - - - - - - - - -" in content:
            self.debug("reference query skipped")
            return ""
        group_name = msg['User'].get('NickName', "")
        group_id = msg['User'].get('UserName', "")
        user_nick = msg.get('ActualNickName', "")
        is_at = msg['IsAt']
        self.info("[_do_handle_group_msg] group_name={}, user_nick={}, is_at={}, group_id={}, ".format(group_name, user_nick, is_at, group_id))
        if len(group_name) <= 0:
            self.info("[_do_handle_group_msg] blank group name and return fast")
            return ""

        config = get_conf("chat.group.{}".format(group_name), default=get_conf("chat.group.*", default=None))
        if config is None:
            self.info("[_do_handle_group_msg] group {} not in group list and ignore".format(group_name))
            return
        if config.get('must_at', True) and not is_at:
            self.info("[_do_handle_group_msg] group {} config must @ but check not @ and return fast".format(group_name))
            return
        self.info("[_do_handle_group_msg] group config {}".format(config))

        prefixs = config.get('prefix', [])
        except_prefixs = config.get('except_prefix', [])
        image_prefixs = get_conf('chat.image.prefix', [])
        prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix, content = parse_prefix(content, prefixs, except_prefixs, image_prefixs)
        self.debug("[_do_handle_group_msg] prefix={}, match_prefix={}, except_prefix={}, match_except_prefix={}, image_prefix={}, \
match_image_prefix={}".format(prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix))
        if not match_prefix:
            self.info("[_do_handle_group_msg] not match prefix={} and return fast".format(prefixs))
            return

        if match_image_prefix:
            thread_pool.submit(self._do_send_img, content, group_id)
        else:
            thread_pool.submit(self._do_send_group, content, msg)

    def _do_send_voice(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = ContextTypeText
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if not reply_text:
                reply_text = "抱歉，我没听清您刚刚说啥，可以再说一次么~"
            wav_file = super().build_text_to_voice(reply_text)
            # 将音频文件转换为amr格式
            # audio = AudioSegment.from_file(wav_file, format="wav")
            # arm_file = wav_file.replace(".wav", ".arm")
            # audio.export(arm_file, format='amr')
            self.send_file(wav_file, reply_user_id)
            # 清除缓存文件
            # os.remove(wav_file)
            # os.remove(arm_file)
        except Exception as e:
            self.error(e)

    def _do_send_text(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = ContextTypeText
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if not reply_text:
                reply_text = "抱歉，我没听清您刚刚说啥，可以再说一次么~"
            self.send(get_conf("chat.single.reply_prefix") + reply_text, reply_user_id)
        except Exception as e:
            self.error(e)

    def _do_send_img(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = ContextTypeImageCreate
            context['session_id'] = reply_user_id
            img_url = super().build_reply_content(query, context)
            if not img_url:
                self.debug("not get img response url and return")
                return

            # 图片下载
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)

            # 图片发送
            self.send_img(image_storage, reply_user_id)
        except Exception as e:
            self.error(e)

    def _do_send_group(self, query, msg):
        try:
            if not query:
                return
            group_name = msg['User']['NickName']
            group_id = msg['User']['UserName']
            config = get_conf("chat.group.{}".format(group_name), default=get_conf("chat.group.*", default=None))
            if config is None:
                self.debug("group {} not in group list and ignore".format(group_name))
                return

            context = dict()
            context['type'] = ContextTypeText
            context['session_id'] = group_id + "-" + msg['ActualUserName']
            if config.get('all_in_one_session', True):
                context['session_id'] = group_id
            self.debug("group {} session_id={}".format(group_name, context['session_id']))

            reply_text = super().build_reply_content(query, context)
            if not reply_text:
                reply_text = "抱歉，我没听清您刚刚说啥，可以再说一次么~"
            reply_text = '@' + msg['ActualNickName'] + ' ' + reply_text.strip()
            self.send(config.get("reply_prefix", "") + reply_text, group_id)
        except Exception as e:
            self.error(e)
