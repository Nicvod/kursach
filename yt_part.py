import time

from googleapiclient.discovery import build
from yt_auth import Authorize

# Authtorize
credentials = Authorize('client_secret.json')
youtube = build('youtube', 'v3', credentials=credentials)
# user id whose account the bot will work from
bot_usr_id = "UCswp_wV-5vk3hQttSDQsHFQ"
_sleep_time = 1
cur_livestrams = []


class MyMessage:
    def __init__(self, tw_channel, yt_channel, yt_stream_id, author, text):
        self.tw_channel = tw_channel
        self.yt_channel = yt_channel
        self.yt_channel = yt_stream_id
        self.author = author
        self.text = text


def GetLiveStreamId(channel_id):
    next_page_token = None
    while True:
        livestreams = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            eventType='live',
            type='video',
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        for livestream in livestreams['items']:
            if livestream['snippet']['liveBroadcastContent'] == 'live':
                return livestream['id']['videoId']
        next_page_token = livestreams.get('nextPageToken')
        if not next_page_token:
            return None


def GetLiveChatId(live_stream_id):
    stream = youtube.videos().list(
        part="liveStreamingDetails",
        id=live_stream_id,
    )
    response = stream.execute()
    live_chat_id = response['items'][0]['liveStreamingDetails']['activeLiveChatId']
    return live_chat_id


def GetUserName(usr_id):
    channel_details = youtube.channels().list(
        part="snippet",
        id=usr_id,
    )
    response = channel_details.execute()
    usr_name = response['items'][0]['snippet']['title']
    return usr_name


def GetMessages(live_chat_id, next_page_token=None):
    id = 3
    response = None
    while id > 0:
        try:
            request = youtube.liveChatMessages().list(
                liveChatId=live_chat_id,
                part="id,snippet,authorDetails",
                maxResults=2000,  # Максимальное количество результатов, которое можно получить за раз
                pageToken=next_page_token
            )
            response = request.execute()
        except:
            id -= 1
            time.sleep(0.2)
            response = None
        else:
            break
    if response is None:
        return [[], None]
    messages = list()
    for item in response['items']:
        message = item['snippet']['displayMessage']
        author = item['authorDetails']['displayName']
        author_id = item['authorDetails']['channelId']
        if author_id == bot_usr_id:
            continue
        messages.append([author, message])

    last_page_token = None
    if 'nextPageToken' in response:
        last_page_token = response['nextPageToken']
        new_messages = GetMessages(live_chat_id, response['nextPageToken'])
        messages.extend(new_messages[0])
        if new_messages[1] is not None:
            last_page_token = new_messages[1]
    return [messages, last_page_token]


def SendMessage(message):
    yt_stream_id = message.yt_stream_id
    yt_chat_id = GetLiveChatId(yt_stream_id)
    author = message.author
    text = message.text
    reply = youtube.liveChatMessages().insert(
        part="snippet",
        body={
            "snippet": {
                "liveChatId": yt_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": f"{author} send message from TW: {text}",
                }
            }
        }
    )
    reply.execute()


def IsStreamAlive(livestream_id):
    response = youtube.videos().list(
        part='liveStreamingDetails',
        id=livestream_id
    ).execute()
    return 'liveStreamingDetails' in response['items'][0] and 'actualStartTime' in response['items'][0][
        'liveStreamingDetails']
