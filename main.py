from db_part import DbClass
from tg_part import MyTgBot
from tw_part import TwBot
from yt_part import YTBot
from extentions import ThreadCommunication

import asyncio
import threading
from dotenv import load_dotenv
import os

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")
YT_BOT_ID = os.getenv("YT_BOT_ID")

id_form_tg_id = dict()

with DbClass() as acc_db:
    thread_communicator = ThreadCommunication()
    tg_bot = MyTgBot(TG_TOKEN, thread_communicator, acc_db)
    tw_bot = TwBot(token=TWITCH_TOKEN, communicator=thread_communicator)
    yt_bot = YTBot(bot_usr_id=YT_BOT_ID, communicator=thread_communicator)

    def tw_func():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(tw_bot.run())

    def yt_func():
        yt_bot.run()

    def tg_func():
        tg_bot.run()


    tw_thread = threading.Thread(target=tw_func, daemon=False)
    yt_thread = threading.Thread(target=yt_func, daemon=False)
    tg_thread = threading.Thread(target=tg_func, daemon=False)

    tw_thread.start()
    yt_thread.start()
    tg_thread.start()

    tw_thread.join()
    yt_thread.join()
    tg_thread.join()
