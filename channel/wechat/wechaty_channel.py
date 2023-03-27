# encoding:utf-8

"""
wechaty channel
Python Wechaty - https://github.com/wechaty/python-wechaty
"""
import asyncio
import os
import time
import wave
from abc import ABC
from typing import Optional, Union

import pysilk
from pydub import AudioSegment
from wechaty import Wechaty, Contact
from wechaty.user import Message, MiniProgram, UrlLink
from wechaty_puppet import MessageType, FileBox, ScanStatus  # type: ignore

from channel.channel import Channel
from common.const import ChannelTypeWXY
from common.tmp_dir import tmp_path
from common.utils import parse_prefix
from conf.config import get_conf


class WechatyChannel(Channel, ABC):

    def __init__(self):
        super().__init__(ChannelTypeWXY)
        self.name = ChannelTypeWXY

    def startup(self):
        asyncio.run(self.main())

    async def main(self):
        # 使用PadLocal协议 比较稳定(免费web协议 os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '127.0.0.1:8080')
        token = get_conf('wx.puppet_service_token')
        os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = token
        global bot
        bot = Wechaty()

        bot.on('scan', self.on_scan)
        bot.on('login', self.on_login)
        bot.on('message', self.on_message)
        await bot.start()

    async def on_login(self, contact: Contact):
        self.info('login user={}'.format(contact))

    async def on_scan(self, status: ScanStatus, qr_code: Optional[str] = None,
                      data: Optional[str] = None):
        contact = self.Contact.load(self.contact_id)
        self.info('scan user={}, scan status={}, scan qr_code={}'.format(contact, status.name, qr_code))
        # print(f'user <{contact}> scan status: {status.name} , 'f'qr_code: {qr_code}')

    async def on_message(self, msg: Message):
        """
        listen for message event
        """
        from_contact = msg.talker()  # 发送者
        to_contact = msg.to()  # 接收者
        room = msg.room()  # 获取消息来自的群聊. 如果消息不是来自群聊, 则返回None
        from_user_id = from_contact.contact_id  # 发送人id
        to_user_id = to_contact.contact_id  # 接收人id
        content = msg.text()

        mention_content = await msg.mention_text()  # 返回过滤掉@name后的消息

        if msg.type() == MessageType.MESSAGE_TYPE_TEXT:
            prefixs = get_conf('chat.single.prefix', [])
            except_prefixs = get_conf('chat.single.except_prefix', [])
            image_prefixs = get_conf('chat.image.prefix', [])
            prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix, content = parse_prefix(content, prefixs, except_prefixs, image_prefixs)
            self.debug("prefix={}, match_prefix={}, except_prefix={}, match_except_prefix={}, image_prefix={}, \
match_image_prefix={}".format(prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix))
            if not match_prefix:
                self.debug("not match prefix and return fast")
                return
            if room is None:
                if not msg.is_self():
                    # 好友向自己发送消息
                    if match_image_prefix:
                        await self._do_send_img(content, from_user_id)
                    else:
                        await self._do_send(content, from_user_id)
                elif msg.is_self():
                    # 自己给好友发送消息
                    if match_image_prefix:
                        await self._do_send_img(content, to_user_id)
                    else:
                        await self._do_send(content, to_user_id)
            else:
                # 群组&文本消息
                room_id = room.room_id
                room_name = await room.topic()
                from_user_id = from_contact.contact_id
                from_user_name = from_contact.name
                is_at = await msg.mention_self()
                content = mention_content
                config = get_conf("chat.group.{}".format(room_name), default=get_conf("chat.group.*", default=None))
                if config is None:
                    self.debug("room={} not in group list and ignore".format(room_name))
                    return
                if config.get('must_at', False) and not is_at:
                    self.debug("room={} must @ but check not @ and return fast".format(room_name))
                    return

                prefixs = config.get('prefix', [])
                except_prefixs = config.get('except_prefix', [])
                image_prefixs = get_conf('chat.image.prefix')
                prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix, content = parse_prefix(content, prefixs, except_prefixs, image_prefixs)
                self.debug("prefix={}, match_prefix={}, except_prefix={}, match_except_prefix={}, image_prefix={}, \
match_image_prefix={}".format(prefix, match_prefix, except_prefix, match_except_prefix, image_prefix, match_image_prefix))
                if not match_prefix:
                    self.debug("not match prefix and return fast")
                    return

                if match_image_prefix:
                    await self._do_send_group_img(content, room_id)
                else:
                    await self._do_send_group(content, room_id, room_name, from_user_id, from_user_name)
        elif msg.type() == MessageType.MESSAGE_TYPE_AUDIO:
            if room is None:
                if not get_conf('single_speech_recognition'):
                    return
                # 下载语音文件
                voice_file = await msg.to_file_box()
                silk_file = os.path.join(tmp_path(), voice_file.name)
                await voice_file.to_file(silk_file)
                self.info("receive bot_voice file: " + silk_file)
                # 将文件转成wav格式音频
                wav_file = silk_file.replace(".slk", ".wav")
                with open(silk_file, 'rb') as f:
                    silk_data = f.read()
                pcm_data = pysilk.decode(silk_data)

                with wave.open(wav_file, 'wb') as wav_data:
                    wav_data.setnchannels(1)
                    wav_data.setsampwidth(2)
                    wav_data.setframerate(24000)
                    wav_data.writeframes(pcm_data)
                if os.path.exists(wav_file):
                    converter_state = "true"  # 转换wav成功
                else:
                    converter_state = "false"  # 转换wav失败
                self.info("receive bot_voice converter: " + converter_state)

                # 语音识别为文本
                query = super().build_voice_to_text(wav_file)

                if not msg.is_self():
                    if get_conf('voice_reply_voice'):
                        await self._do_send_voice(query, from_user_id)
                    else:
                        await self._do_send(query, from_user_id)
                else:
                    if get_conf('voice_reply_voice'):
                        await self._do_send_voice(query, to_user_id)
                    else:
                        await self._do_send(query, to_user_id)
                # 清除缓存文件
                # os.remove(wav_file)
                # os.remove(silk_file)
            else:
                if not get_conf('group_speech_recognition'):
                    return
                pass

    async def send(self, message: Union[str, Message, FileBox, Contact, UrlLink, MiniProgram], receiver):
        self.debug('sendMsg={}, receiver={}'.format(message, receiver))
        if receiver:
            contact = await bot.Contact.find(receiver)
            await contact.say(message)

    async def send_group(self, message: Union[str, Message, FileBox, Contact, UrlLink, MiniProgram], receiver):
        self.debug('sendGroupMsg={}, receiver={}'.format(message, receiver))
        if receiver:
            room = await bot.Room.find(receiver)
            await room.say(message)

    async def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                await self.send(get_conf("chat.single.reply_prefix") + reply_text, reply_user_id)
            else:
                await self.send(get_conf("chat.single.reply_prefix") + "抱歉，我没听清您刚刚说啥，可以再说一次么~", reply_user_id)
        except Exception as e:
            self.error(e)

    async def _do_send_voice(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                # 转换 mp3 文件为 silk 格式
                wav_file = super().build_text_to_voice(reply_text)
                silk_file = wav_file.replace(".wav", ".silk")
                # Load the WAV file
                audio = AudioSegment.from_file(wav_file, format="wav")
                # Encode to SILK format
                silk_data = pysilk.encode(audio, 24000)
                # Save the silk file
                with open(silk_file, "wb") as f:
                    f.write(silk_data)
                # 发送语音
                t = int(time.time())
                file_box = FileBox.from_file(silk_file, name=str(t) + '.silk')
                await self.send(file_box, reply_user_id)
                # 清除缓存文件
                # os.remove(wav_file)
                # os.remove(silk_file)
        except Exception as e:
            self.error(e)

    async def _do_send_img(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_url = super().build_reply_content(query, context)
            if not img_url:
                return
            # 图片下载
            # pic_res = requests.get(img_url, stream=True)
            # image_storage = io.BytesIO()
            # for block in pic_res.iter_content(1024):
            #     image_storage.write(block)
            # image_storage.seek(0)

            # 图片发送
            self.info('sendImage, receiver={}'.format(reply_user_id))
            t = int(time.time())
            file_box = FileBox.from_url(url=img_url, name=str(t) + '.png')
            await self.send(file_box, reply_user_id)
        except Exception as e:
            self.error(e)

    async def _do_send_group(self, query, group_id, group_name, group_user_id, group_user_name):
        if not query:
            return
        context = dict()
        config = get_conf("chat.group.{}".format(group_name), default=get_conf("chat.group.*", default=None))
        if config is None:
            return

        all_in_one_session = config.get('all_in_one_session', True)
        if all_in_one_session:
            context['session_id'] = str(group_id)
        else:
            context['session_id'] = str(group_id) + '-' + str(group_user_id)
        reply_text = super().build_reply_content(query, context)
        if reply_text:
            reply_text = '@' + group_user_name + ' ' + reply_text.strip()
            await self.send_group(config.get("reply_prefix", "") + reply_text, group_id)

    async def _do_send_group_img(self, query, reply_room_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_url = super().build_reply_content(query, context)
            if not img_url:
                return
            # 图片发送
            self.info('sendImage, receiver={}'.format(reply_room_id))
            t = int(time.time())
            file_box = FileBox.from_url(url=img_url, name=str(t) + '.png')
            await self.send_group(file_box, reply_room_id)
        except Exception as e:
            self.error(e)
