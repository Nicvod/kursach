import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from yt_auth import Authorize
from extentions import MyMessage, HostsUnion, ThreadCommunication
from typing import List
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('YT.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class YTMessage:
    def __init__(self, author, text):
        self.author = author
        self.text = text


class YTBot:

    def __init__(self, bot_usr_id, communicator: ThreadCommunication):
        self.yt_from_tw = dict()
        self.chat_id = dict()
        self.last_published = dict()
        self.page_tokens = dict()

        self.communicator = communicator
        # user id whose account the bot will work from
        self.bot_usr_id = bot_usr_id

        #auth
        credentials = Authorize('client_secret.json')
        self.youtube = build('youtube', 'v3', credentials=credentials)
        _sleep_time = 1

    def GetLiveChatId(self, live_stream_id):
        if live_stream_id not in self.chat_id:
            stream = self.youtube.videos().list(
                part="liveStreamingDetails",
                id=live_stream_id,
            )
            response = stream.execute()
            live_chat_id = response['items'][0]['liveStreamingDetails']['activeLiveChatId']
            self.chat_id[live_stream_id] = live_chat_id
        return self.chat_id[live_stream_id]

    def SendMessage(self, message: MyMessage):
        live_stream_id = self.yt_from_tw[message.host_info]
        chat_id = self.GetLiveChatId(live_stream_id)
        author = message.author
        text = message.text
        logger.info(f"Before sending for youtube: {author} send message from {message.host_name}: {text},\
                                    chat_id: {chat_id}")
        reply = self.youtube.liveChatMessages().insert(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": f"{author} send message from {message.host_name}: {text}",
                    }
                }
            }
        )
        reply.execute()
        logger.info(f"After sending for youtube: {author} send message from {message.host_name}: {text},\
                                    chat_id: {chat_id}")

    def GetMessages(self, live_stream_id, chat_id) -> List['YTMessage']:
        messages = list()
        last_published = self.last_published[live_stream_id]
        next_page_token = self.page_tokens[live_stream_id]

        while True:
            request = self.youtube.liveChatMessages().list(
                liveChatId=chat_id,
                part="snippet,authorDetails",
                maxResults=100,
                pageToken=next_page_token
            )
            response = request.execute()
            if response is None or "items" not in response:
                break
            if len(response['items']) == 0:
                break
            for item in response['items']:
                try:
                    text = item['snippet']['displayMessage']
                    author = item['authorDetails']['displayName']
                    author_id = item['authorDetails']['channelId']
                    published_at = item['snippet']['publishedAt']
                    if published_at <= last_published:
                        continue
                    if author_id == self.bot_usr_id:
                        continue
                    last_published = published_at
                    messages.append(YTMessage(author=author, text=text))
                except Exception as e:
                    logger.info(f"Ошибка: {e}")
                    continue
            if 'nextPageToken' in response:
                next_page_token = response['nextPageToken']
                # self.page_tokens[live_stream_id] = next_page_token
            else:
                break
            time.sleep(2)
        self.last_published[live_stream_id] = last_published
        return messages

    def ReadMessages(self):
        for tw_acc in self.yt_from_tw:
            logger.info(f"Read for tw: {tw_acc}")
            live_stream_id = self.yt_from_tw[tw_acc]
            chat_id = self.chat_id[live_stream_id]
            messages = self.GetMessages(live_stream_id=live_stream_id, chat_id=chat_id)
            if len(messages) == 0:
                continue
            for message in messages:
                self.communicator.add_message("TW", MyMessage(host_name="YT", host_info=live_stream_id,
                                                              author=message.author, text=message.text))

    def run(self):
        while True:
            while True:
                host_info = self.communicator.get_hosts_info("YT")
                if host_info is None:
                    break
                if host_info.status:
                    self.yt_from_tw[host_info.tw_info] = host_info.yt_info
                    self.chat_id[host_info.yt_info] = self.GetLiveChatId(host_info.yt_info)
                    self.last_published[host_info.yt_info] = "2000-01-01T00:00:00.0Z"
                    self.page_tokens[host_info.yt_info] = None
                else:
                    self.yt_from_tw.pop(host_info.tw_info, None)
                    self.chat_id.pop(host_info.yt_info, None)
                    self.last_published.pop(host_info.yt_info, None)
                    self.page_tokens.pop(host_info.yt_info, None)
            while True:
                message = self.communicator.get_message("YT")
                if message is None:
                    break
                self.SendMessage(message=message)
            self.ReadMessages()
            time.sleep(1)
