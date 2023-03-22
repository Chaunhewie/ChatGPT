# encoding:utf-8

"""
wechat channel
"""
import io
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

import itchat
import requests
from itchat.content import *

from channel.channel import Channel
from common.const import ChannelTypeWX
from common.tmp_dir import TmpDir
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
        itchat.auto_login(enableCmdQR=2, hotReload=get_conf('wx.hot_reload', default=False))

        # start message listener
        itchat.run()

    def send(self, msg, receiver):
        itchat.send(msg, toUserName=receiver)
        self.debug('sendMsg={}, receiver={}'.format(msg, receiver))

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
        other_user_id = msg['User']['UserName']  # 聊天对方的id

        # from_user_id == other_user_id 好友向自己发送消息
        # to_user_id == other_user_id 自己给好友发送消息
        self.debug("from user {} -> to user {}, other user is {}".format(from_user_id, to_user_id, other_user_id))

        if len(other_user_id) <= 0:
            self.debug("blank other user id and return fast")
            return ""

        # 下载音频并处理为文字
        file_name = TmpDir().path() + msg['FileName']
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
        self.debug("group_name={}, group_id={}".format(group_name, group_id))
        if len(group_name) <= 0:
            self.debug("blank group name and return fast")
            return ""

        config = get_conf("chat.group.{}".format(group_name), default=None)
        if config is None:
            self.debug("group name={} not in group list and ignore".format(group_name))
            return

        file_name = TmpDir().path() + msg['FileName']
        msg.download(file_name)
        query = super().build_voice_to_text(file_name)
        if get_conf('voice_reply_voice'):
            thread_pool.submit(self._do_send_voice, query, group_id)
        else:
            thread_pool.submit(self._do_send_group, query, msg)

    def handle_single_msg(self, msg):
        content = msg['Text']
        self.debug("receive single text msg: " + content)
        self._do_handle_single_msg(msg, content)

    def _do_handle_single_msg(self, msg, content):
        if "- - - - - - - - - - - - - - -" in content:
            self.debug("reference query skipped")
            return
        from_user_id = msg['FromUserName']  # 发送人id
        to_user_id = msg['ToUserName']  # 接收人id
        other_user_id = msg['User']['UserName']  # 聊天对方的id

        # from_user_id == other_user_id 好友向自己发送消息
        # to_user_id == other_user_id 自己给好友发送消息
        self.debug("from user {} -> to user {}, other user is {}".format(from_user_id, to_user_id, other_user_id))

        if len(other_user_id) <= 0:
            self.debug("blank other user id and return fast")
            return ""

        prefixs = get_conf('chat.single.prefix')
        image_prefixs = get_conf('chat.image.prefix')

        prefix, match_prefix, image_prefix, match_image_prefix, content = parse_prefix(content, prefixs, image_prefixs)
        self.debug("prefix={}, match_prefix={}, image_prefix={}, match_image_prefix={}".format(prefix, match_prefix, image_prefix, match_image_prefix))

        if not match_prefix:
            self.debug("not match prefix and return fast")
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

        self.debug("receive group text msg: " + content)
        self._do_handle_group_msg(msg, content)

    def _do_handle_group_msg(self, msg, content):
        if "- - - - - - - - - - - - - - -" in content:
            self.debug("reference query skipped")
            return ""
        group_name = msg['User'].get('NickName', "")
        group_id = msg['User'].get('UserName', "")
        is_at = msg['IsAt']
        self.debug("group_name={}, group_id={}, is_at={}".format(group_name, group_id, is_at))
        if len(group_name) <= 0:
            self.debug("blank group name and return fast")
            return ""

        config = get_conf("chat.group.{}".format(group_name), default=None)
        if config is None:
            self.debug("group {} not in group list and ignore".format(group_name))
            return
        if config.get('must_at', True) and not is_at:
            self.debug("group {} config must @ but check not @ and return fast".format(group_name))
            return

        prefixs = config.get('prefix', [])
        image_prefixs = get_conf('chat.image.prefix')
        prefix, match_prefix, image_prefix, match_image_prefix, content = parse_prefix(content, prefixs, image_prefixs)
        self.debug("prefix={}, match_prefix={}, image_prefix={}, match_image_prefix={}".format(prefix, match_prefix, image_prefix, match_image_prefix))
        if not match_prefix:
            self.debug("not match prefix={} and return fast".format(prefixs))
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
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if not reply_text:
                reply_text = "抱歉，我没听清您刚刚说啥，可以再说一次么~"
            replyFile = super().build_text_to_voice(reply_text)
            self.send(replyFile, reply_user_id)
        except Exception as e:
            self.error(e)

    def _do_send_text(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
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
            context['type'] = 'IMAGE_CREATE'
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
            config = get_conf("chat.group.{}".format(group_name), default=None)
            if config is None:
                self.debug("group {} not in group list and ignore".format(group_name))
                return

            context = dict()
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
