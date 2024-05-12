import asyncio
import time
from twitchio.ext import commands
from extentions import MyMessage, HostsUnion, ThreadCommunication
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('TW.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

class TwBot(commands.Bot):
    def __init__(self, token, communicator: ThreadCommunication):
        super().__init__(token=token, prefix='?', initial_channels=[])
        self.communicator = communicator
        self.loop.create_task(self.endless_loop())
        self.tw_from_yt = dict()
        self.fl = False

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return
        logger.info(f"New from TW message TW_info: {message.channel.name}, author: {message.author.name}, text:\
                                                {message.content}")
        self.communicator.add_message(thread_name="YT", item=MyMessage(host_name="TW", host_info=message.channel.name,
                                                                       author=message.author.name, text=message.content))
        return

    async def endless_loop(self):
        if self.fl:
            return
        self.fl = True
        while True:
            await self.update_func()
            await asyncio.sleep(1)

    async def update_func(self):
        while True:
            host_info = self.communicator.get_hosts_info("TW")
            if host_info is None:
                break
            logger.info(f"TW channel update tw_info: {host_info.tw_info}, yt_info: {host_info.yt_info}, status:\
                                            {host_info.status}")
            if host_info.status:
                self.tw_from_yt[host_info.yt_info] = host_info.tw_info
                await self.join_channels([host_info.tw_info])
            else:
                self.tw_from_yt.pop(host_info.yt_info, None)
                await self.part_channels([host_info.tw_info])
        while True:
            message = self.communicator.get_message("TW")
            if message is None:
                break
            if message.host_info not in self.tw_from_yt:
                continue
            tw_channel = self.tw_from_yt[message.host_info]
            channel = self.get_channel(tw_channel)
            if channel is None:
                continue
            author = message.author
            text = message.text
            self.last_send = time.time()
            await channel.send(f"{author} sent message from {message.host_name}: {text}")
            logger.info(f"Sent message for tw, host: {message.host_name}, author: {author}, text: {text} ")

