# encoding:utf-8

"""
wechat channel
"""
import io
import json
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

import itchat
import requests
from itchat.content import *

from channel.channel import Channel
from common.const import ChannelTypeWX
from common.tmp_dir import TmpDir
from conf.config import get_conf

thread_pool = ThreadPoolExecutor(max_workers=8)


@itchat.msg_register(TEXT)
def handler_single_msg(msg):
    WechatChannel().handle_text(msg)
    return None


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_group_msg(msg):
    WechatChannel().handle_group(msg)
    return None


@itchat.msg_register(VOICE)
def handler_single_voice(msg):
    WechatChannel().handle_voice(msg)
    return None


@itchat.msg_register(VOICE, isGroupChat=True)
def handler_single_voice(msg):
    WechatChannel().handle_group_voice(msg)
    return None


class WechatChannel(Channel, ABC):
    def __init__(self):
        super().__init__(ChannelTypeWX)
        self.name = ChannelTypeWX
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login(enableCmdQR=2, hotReload=get_conf('wx.hot_reload', default=False))

        # start message listener
        itchat.run()

    def handle_voice(self, msg):
        if not get_conf('speech_recognition'):
            return
        self.debug("receive bot_voice msg: " + msg['FileName'])
        thread_pool.submit(self._do_handle_voice, msg)

    def _do_handle_voice(self, msg):
        from_user_id = msg['FromUserName']
        other_user_id = msg['User']['UserName']
        if from_user_id == other_user_id:
            file_name = TmpDir().path() + msg['FileName']
            msg.download(file_name)
            query = super().build_voice_to_text(file_name)
            if get_conf('voice_reply_voice'):
                self._do_send_voice(query, from_user_id)
            else:
                self._do_send_text(query, from_user_id)

    def handle_group_voice(self, msg):
        if not get_conf('speech_recognition'):
            return
        self.debug("receive bot_voice msg: " + msg['FileName'])
        thread_pool.submit(self._do_handle_group_voice, msg)

    def _do_handle_group_voice(self, msg):
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        config = get_conf("chat.group.{}".format(group_name), default=None)
        if config is None:
            self.debug("group={} not in group list and ignore".format(group_name))
            return
        file_name = TmpDir().path() + msg['FileName']
        msg.download(file_name)
        query = super().build_voice_to_text(file_name)
        if get_conf('voice_reply_voice'):
            self._do_send_voice(query, group_id)
        else:
            self._do_send_group(query, msg)

    def handle_text(self, msg):
        self.debug("receive text msg: " + json.dumps(msg, ensure_ascii=False))
        content = msg['Text']
        self._handle_single_msg(msg, content)

    def _handle_single_msg(self, msg, content):
        if "- - - - - - - - - - - - - - -" in content:
            self.debug("reference query skipped")
            return
        from_user_id = msg['FromUserName']
        to_user_id = msg['ToUserName']  # 接收人id
        other_user_id = msg['User']['UserName']  # 对方id
        self.debug("user {} -> user {}, other_user_id={}".format(from_user_id, to_user_id, other_user_id))

        prefixs = get_conf('chat.single.prefix')
        prefix, match_prefix = self.check_prefix(content, prefixs)
        if not match_prefix:
            self.debug("not match prefix and return fast")
            return
        if len(prefix) > 0:
            str_list = content.split(prefix, 1)
            if len(str_list) == 2:
                content = str_list[1].strip()

        image_prefixs = get_conf('chat.image.prefix')
        image_prefix, match_image_prefix = self.check_prefix(content, image_prefixs)
        if len(image_prefix) > 0:
            str_list = content.split(image_prefix, 1)
            if len(str_list) == 2:
                content = str_list[1].strip()

        if from_user_id == other_user_id:
            # 好友向自己发送消息
            if match_image_prefix:
                thread_pool.submit(self._do_send_img, content, from_user_id)
            else:
                thread_pool.submit(self._do_send_text, content, from_user_id)
        elif to_user_id == other_user_id:
            # 自己给好友发送消息
            if match_image_prefix:
                thread_pool.submit(self._do_send_img, content, to_user_id)
            else:
                thread_pool.submit(self._do_send_text, content, to_user_id)

    def handle_group(self, msg):
        self.debug("receive group msg: " + json.dumps(msg, ensure_ascii=False))
        content = msg['Content']
        content_list = content.split(' ', 1)
        context_special_list = content.split('\u2005', 1)
        if len(context_special_list) == 2:
            content = context_special_list[1]
        elif len(content_list) == 2:
            content = content_list[1]
        if "- - - - - - - - - - - - - - -" in content:
            self.debug("reference query skipped")
            return ""
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        is_at = msg['IsAt']
        self.debug("group_name={}, group_id={}, is_at={}".format(group_name, group_id, is_at))
        if not group_name:
            self.debug("blank group name and return fast")
            return ""

        config = get_conf("chat.group.{}".format(group_name), default=None)
        if config is None:
            self.debug("group={} not in group list and ignore".format(group_name))
            return
        if config.get('must_at', False) and not is_at:
            self.debug("group={} must @ but check not @ and return fast".format(group_name))
            return

        prefixs = config.get('prefix', [])
        prefix, match_prefix = self.check_prefix(content, prefixs)
        if not match_prefix:
            self.debug("not match prefix={} and return fast".format(prefixs))
            return
        if len(prefix) > 0:
            str_list = content.split(prefix, 1)
            if len(str_list) == 2:
                content = str_list[1].strip()

        image_prefixs = get_conf('chat.image.prefix')
        image_prefix, match_image_prefix = self.check_prefix(content, image_prefixs)
        if len(image_prefix) > 0:
            str_list = content.split(image_prefix, 1)
            if len(str_list) == 2:
                content = str_list[1].strip()

        self.debug("match_prefix={}".format(match_prefix))
        if match_image_prefix:
            thread_pool.submit(self._do_send_img, content, group_id)
        else:
            thread_pool.submit(self._do_send_group, content, msg)

    def send(self, msg, receiver):
        itchat.send(msg, toUserName=receiver)
        self.debug('sendMsg={}, receiver={}'.format(msg, receiver))

    def _do_send_voice(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                replyFile = super().build_text_to_voice(reply_text)
                itchat.send(replyFile, toUserName=reply_user_id)
                self.debug('sendFile={}, receiver={}'.format(replyFile, reply_user_id))
        except Exception as e:
            self.error(e)

    def _do_send_text(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                self.send(get_conf("chat.single.reply_prefix") + reply_text, reply_user_id)
        except Exception as e:
            self.error(e)

    def _do_send_img(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_url = super().build_reply_content(query, context)
            if not img_url:
                return

            # 图片下载
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)

            # 图片发送
            itchat.send_image(image_storage, reply_user_id)
            self.debug('sendImage, receiver={}'.format(reply_user_id))
        except Exception as e:
            self.error(e)

    def _do_send_group(self, query, msg):
        if not query:
            return
        context = dict()
        group_name = msg['User']['NickName']
        group_id = msg['User']['UserName']
        config = get_conf("chat.group.{}".format(group_name), default=None)
        if config is None:
            self.debug("group={} not in group list and ignore".format(group_name))
            return
        all_in_one_session = config.get('all_in_one_session', True)
        if all_in_one_session:
            context['session_id'] = group_id
        else:
            context['session_id'] = msg['ActualUserName']
        self.debug("session_id={}".format(context['session_id']))
        reply_text = super().build_reply_content(query, context)
        if reply_text:
            reply_text = '@' + msg['ActualNickName'] + ' ' + reply_text.strip()
            self.send(config.get("reply_prefix", "") + reply_text, group_id)

    @staticmethod
    def check_prefix(content, prefix_list):
        if not prefix_list:
            return "", False
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix, True
        return "", False

    @staticmethod
    def check_contain(content, keyword_list):
        if not keyword_list:
            return False
        for ky in keyword_list:
            if content.find(ky) != -1:
                return ky, True
        return "", False
