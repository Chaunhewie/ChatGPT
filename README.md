# 简介

NOTICE：Fork Of [zhayujie/chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat) ，用于搭建自己的ChatGPT聊天机器人。

基于ChatGPT的微信聊天机器人，通过 [ChatGPT](https://github.com/openai/openai-python) 接口生成对话内容，使用 [itchat](https://github.com/littlecodersh/ItChat) 实现微信消息的接收和自动回复。已实现的特性如下：

- [x] **文本对话：** 接收私聊及群组中的微信消息，使用ChatGPT生成回复内容，完成自动回复
- [x] **规则定制化：** 支持私聊中按指定规则触发自动回复，支持对群组设置自动回复白名单，支持群组维度的自定义触发键配置
- [x] **多账号：** 支持多微信账号同时运行
- [x] **图片生成：** 支持根据描述生成图片，并自动发送至个人聊天或群聊
- [x] **上下文记忆**：支持多轮对话记忆，且为每个好友维护独立的上下会话
- [x] **语音识别：** 支持接收和处理语音消息，通过文字或语音回复
    - 语音回复需要安装以下语音能力，否则需要更换引擎：
        ```
        brew install espeak
        brew install swig
        brew install ffmpeg
        ```
