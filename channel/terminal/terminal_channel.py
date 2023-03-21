import sys
from abc import ABC

from channel.channel import Channel
from common.const import ChannelTypeTerminal


class TerminalChannel(Channel, ABC):
    def __init__(self):
        super().__init__(ChannelTypeTerminal)
        self.name = ChannelTypeTerminal

    def startup(self):
        context = {"from_user_id": "User"}
        print("\nPlease input your question")
        while True:
            try:
                prompt = self.get_input("User:\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()

            print("Bot:")
            sys.stdout.flush()
            for res in super().build_reply_content(prompt, context):
                print(res, end="")
                sys.stdout.flush()
            print("\n")

    @staticmethod
    def get_input(prompt):
        """
        Multi-line input function
        """
        print(prompt, end="")
        line = input()
        return line
