import asyncio
from twitchio.ext import commands
from extentions import MyMessage, HostsUnion, ThreadCommunication


class TwBot(commands.Bot):
    def __init__(self, token, communicator: ThreadCommunication):
        super().__init__(token=token, prefix='?', initial_channels=[])
        self.communicator = communicator
        self.loop.create_task(self.endless_loop())
        self.tw_from_yt = dict()

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return
        self.communicator.add_message(thread_name="YT", item=MyMessage(host_name="TW", host_info=message.channel.name,
                                                                       author=message.author.name, text=message.content))
        return

    async def endless_loop(self):
        while True:
            await self.update_func()
            await asyncio.sleep(2)

    async def update_func(self):
        while True:
            host_info = self.communicator.get_hosts_info("TW")
            if host_info is None:
                break
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
            tw_channel = self.tw_from_yt[message.host_info]
            author = message.author
            text = message.text
            channel = self.get_channel(tw_channel)
            if channel is None:
                continue
            await channel.send(f"{author} send message from {message.host_name}: {text}")

