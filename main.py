# from aiologger.loggers.json import JsonLogger
import time

import db_part
import yt_part
from yt_part import MyMessage

import asyncio
import telebot
from telebot import types
import threading
from twitchio.ext import commands
import queue
from dotenv import load_dotenv
import os

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")

id_form_tg_id = dict()
# logger = JsonLogger.with_default_handlers(name='my_logger')

with db_part.DbClass() as acc_db:
    bot = telebot.TeleBot(TG_TOKEN)
    add_accs_tw = queue.Queue()
    del_accs_tw = queue.Queue()
    add_accs_yt = queue.Queue()
    del_accs_yt = queue.Queue()
    messages_for_tw = queue.Queue()
    messages_for_yt = queue.Queue()
    cur_livestreams = set()


    class Bot(commands.Bot):
        def __init__(self):
            super().__init__(token=TWITCH_TOKEN, prefix='?', initial_channels=[])
            self.loop.create_task(self.endless_loop())
            self.yt_id_from_tw_channel = dict()

        async def event_ready(self):
            print(f'Logged in as | {self.nick}')
            print(f'User id is | {self.user_id}')

        async def event_message(self, message):
            print(message.author.name, message.channel.name, message.content, message.echo)
            if message.echo:
                return
            yt_id = self.yt_id_from_tw_channel[message.channel.name]
            messages_for_yt.put(MyMessage(tw_channel=message.channel.name, yt_channel=yt_id[0], yt_stream_id=yt_id[1],
                                          author=message.author.name, text=message.content))
            return

        async def endless_loop(self):
            while True:
                await self.update_func()
                await asyncio.sleep(2)

        async def update_func(self):
            while not add_accs_tw.empty():
                acc = add_accs_tw.get()
                print("add_acc_tw", acc)
                self.yt_id_from_tw_channel[acc[0]] = acc[1]
                await self.join_channels([acc[0]])
            while not del_accs_tw.empty():
                acc = del_accs_tw.get()
                self.yt_id_from_tw_channel.pop(acc[0], None)
                await self.part_channels([acc[0]])
            while not messages_for_tw:
                message = messages_for_tw.get()
                print(f'Message for TW: {message.author}, {message.text}')
                tw_channel = message.tw_channel
                author = message.author
                text = message.text
                channel = self.get_channel(tw_channel)
                if channel is None:
                    continue
                await channel.send(f"{author} send message from YT: {text}")


    def MakeStartKeyBoard():
        start_keyboard = types.InlineKeyboardMarkup()
        tw_btn = types.InlineKeyboardButton('Прикрепить аккаунт Twitch', callback_data='TW_reg')
        yt_btn = types.InlineKeyboardButton('Прикрепить аккаут YouTube', callback_data='YT_reg')
        start_keyboard.add(tw_btn, yt_btn)
        help_info = types.InlineKeyboardButton('Информация о подключённых аккаунтах', callback_data='help')
        start_keyboard.add(help_info)
        start_btn = types.InlineKeyboardButton('Начать пересылку сообщений на стримах',
                                               callback_data='start_livestream')
        stop_btn = types.InlineKeyboardButton('Остановить пересылку сообщений на стримах',
                                              callback_data='stop_livestream')
        start_keyboard.add(start_btn, stop_btn)
        return start_keyboard


    def GetUserId(tg_id):
        if not (tg_id in id_form_tg_id):
            usr_id = acc_db.GetIdFromUsr(tg_id)[0]
            id_form_tg_id[tg_id] = usr_id
        return id_form_tg_id[tg_id]


    @bot.message_handler(commands=['start'])
    def Start(message):
        bot.send_message(message.chat.id, 'Что хотите сделать?', reply_markup=MakeStartKeyBoard())


    def TwitchReg(message):
        usr_id = GetUserId(message.from_user.id)
        acc_db.ChangeTwAcc(usr_id, message.text)
        bot.send_message(message.chat.id, 'Твич аккаунт успешно привязан, что будем делать дальше?',
                         reply_markup=MakeStartKeyBoard())
        # logger.info( f'Пользователь с td_id {message.from_user.id} и с id {usr_id} зарегистрировал аккаунт твича: {
        # message.text}')


    def YouTubeReg(message):
        usr_id = GetUserId(message.from_user.id)
        acc_db.ChangeYtAcc(usr_id, message.text)
        bot.send_message(message.chat.id, 'Ютуб аккаунт успешно привязан, что будем делать дальше?',
                         reply_markup=MakeStartKeyBoard())
        # logger.info( f'Пользователь с td_id {message.from_user.id} и с id {usr_id} зарегистрировал аккаунт ютуба: {
        # message.text}')


    def TwitchAdd(call):
        usr_id = GetUserId(call.from_user.id)
        tw_acc = acc_db.GetTwAcc(usr_id)[0]
        if tw_acc is not None:
            # Checking that the account has already been added
            markup = types.InlineKeyboardMarkup()
            yes_btn = types.InlineKeyboardButton('Да', callback_data='tw_confirm')
            markup.add(yes_btn)
            bst_btn = types.InlineKeyboardButton('Нет', callback_data='back_to_start')
            markup.add(bst_btn)
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} и id {usr_id} возможно изменит аккаунт твича')
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'Вы уже прикрепляли аккаунт: {tw_acc}, хотите его изменить?',
                                  reply_markup=markup)
        else:
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} и id {usr_id} хочет зарегистрировать аккаунт твича')
            bot.send_message(chat_id=call.message.chat.id, text="Введите название твич аккаунта")
            bot.register_next_step_handler(call.message, TwitchReg)


    def YouTubeAdd(call):
        usr_id = GetUserId(call.from_user.id)
        yt_acc = acc_db.GetYtAcc(usr_id)[0]

        if yt_acc is not None:
            # Checking that the account has already been added
            markup = types.InlineKeyboardMarkup()
            yes_btn = types.InlineKeyboardButton('Да', callback_data='yt_confirm')
            markup.add(yes_btn)
            bst_btn = types.InlineKeyboardButton('Нет', callback_data='back_to_start')
            markup.add(bst_btn)
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} и id {usr_id} возможно изменит аккаунт ютуба')
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'Вы уже прикрепляли аккаунт: {yt_acc}, хотите его изменить?',
                                  reply_markup=markup)
        else:
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} и id {usr_id} хочет зарегистрировать аккаунт ютуба')
            bot.send_message(chat_id=call.message.chat.id, text="Введите индификатор ютуб аккаунта. "
                                                                "Пример индификатора: "
                                                                "https://www.youtube.com/channel"
                                                                "/UCfYicHH5s0wEutxTH0YcURQ\n"
                                                                "<pre>UCfYicHH5s0wEutxTH0YcURQ</pre>",
                             parse_mode='HTML')
            bot.register_next_step_handler(call.message, YouTubeReg)


    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        if call.data == 'TW_reg':
            TwitchAdd(call)
        elif call.data == 'YT_reg':
            YouTubeAdd(call)
        elif call.data == 'back_to_start':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Что хотите сделать?', reply_markup=MakeStartKeyBoard())
        elif call.data == "tw_confirm":
            bot.send_message(chat_id=call.message.chat.id, text="Введите название твич аккаунта")
            bot.register_next_step_handler(call.message, TwitchReg)
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} меняет уже зарегестрированный аккаунт твича')
        elif call.data == "yt_confirm":
            bot.send_message(chat_id=call.message.chat.id, text="Введите индификатор ютуб аккаунта. "
                                                                "Пример индификатора: "
                                                                "https://www.youtube.com/channel"
                                                                "/UCfYicHH5s0wEutxTH0YcURQ\n"
                                                                "<pre>UCfYicHH5s0wEutxTH0YcURQ</pre>",
                             parse_mode='HTML')
            bot.register_next_step_handler(call.message, YouTubeReg)
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} меняет уже зарегестрированный аккаунт ютуба')
        elif call.data == "start_livestream":
            usr_id = GetUserId(call.from_user.id)
            tw_acc = acc_db.GetTwAcc(usr_id)[0]
            yt_acc = acc_db.GetYtAcc(usr_id)[0]
            # logger.info(
            #     f'Пользователь с td_id {call.from_user.id} и id {usr_id} запускает стрим с tw {tw_acc} и yt {yt_acc}')
            if tw_acc is None or yt_acc is None:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Не все аккаунты ещё привязаны", reply_markup=MakeStartKeyBoard())
            elif call.from_user.id in cur_livestreams:
                if call.message.text != "Вы уже начали пересылку сообщений":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text="Вы уже начали пересылку сообщений", reply_markup=MakeStartKeyBoard())
            else:
                live_stream_id = yt_part.GetLiveStreamId(yt_acc)
                if live_stream_id is None:
                    if call.message.text != "Стрим ещё не начался":
                        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                              text="Стрим ещё не начался", reply_markup=MakeStartKeyBoard())
                else:
                    if call.message.text != "Пересылка сообщений начата":
                        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                              text="Пересылка сообщений начата", reply_markup=MakeStartKeyBoard())
                        cur_livestreams.add(call.from_user.id)
                        add_accs_tw.put((tw_acc, (yt_acc, live_stream_id)))
                        add_accs_yt.put((tw_acc, (yt_acc, live_stream_id)))
        elif call.data == "stop_livestream":
            usr_id = GetUserId(call.from_user.id)
            tw_acc = acc_db.GetTwAcc(usr_id)[0]
            yt_acc = acc_db.GetYtAcc(usr_id)[0]
            if call.from_user.id not in cur_livestreams:
                if call.message.text != "Вы не начинали пересылку сообщений":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text="Вы не начинали пересылку сообщений", reply_markup=MakeStartKeyBoard())
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Пересылка сообщений прекращена", reply_markup=MakeStartKeyBoard())
                cur_livestreams.discard(call.from_user.id)
                del_accs_tw.put((tw_acc, yt_acc))
                del_accs_yt.put((tw_acc, yt_acc))
        elif call.data == "help":
            usr_id = GetUserId(call.from_user.id)
            tw_acc = acc_db.GetTwAcc(usr_id)[0]
            yt_acc = acc_db.GetYtAcc(usr_id)[0]
            bot_message = ""
            if tw_acc is None:
                bot_message += "Твич аккаунт ещё не привязан\n"
            else:
                bot_message += f"Вы привязали твич аккаунт {tw_acc}\n"
            if yt_acc is None:
                bot_message += "Ютуб аккаунт ещё не привязан"
            else:
                bot_message += f"Вы привязали ютуб аккаунт {yt_acc}"
            markup = types.InlineKeyboardMarkup()
            bts_btn = types.InlineKeyboardButton('Вернуться назад', callback_data='back_to_start')
            markup.add(bts_btn)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=bot_message, reply_markup=markup)


    def tw_func():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tw_bot = Bot()
        loop.run_until_complete(tw_bot.run())


    def yt_func():
        yt_chat_id_from_yt_channel = dict()
        yt_stream_id_from_yt_channel = dict()
        tw_channel_from_yt_channel = dict()
        page_token_from_yt_chat_id = dict()
        while True:
            while not add_accs_yt.empty():
                acc = add_accs_yt.get()
                print("add_acc_yt", acc)
                chat_id = yt_part.GetLiveChatId(acc[1][1])
                tw_channel_from_yt_channel[acc[1][0]] = acc[0]
                yt_chat_id_from_yt_channel[acc[1][0]] = chat_id
                yt_stream_id_from_yt_channel[acc[1][0]] = acc[1][1]
                page_token_from_yt_chat_id[chat_id] = None
            while not del_accs_yt.empty():
                acc = del_accs_yt.get()
                chat_id = yt_chat_id_from_yt_channel[acc[1]]
                yt_chat_id_from_yt_channel.pop(acc[1], None)
                yt_stream_id_from_yt_channel.pop(acc[1], None)
                tw_channel_from_yt_channel.pop(acc[1], None)
                page_token_from_yt_chat_id.pop(chat_id, None)
            while not messages_for_yt.empty():
                message = messages_for_yt.get()
                print(f'Message for YT: {message.author}, {message.text}')
                yt_channel = message.yt_channel
                if yt_channel not in yt_chat_id_from_yt_channel:
                    continue
                yt_part.SendMessage(message)
            for yt_channel in yt_chat_id_from_yt_channel:
                print(f"YT_CHN {yt_channel}")
                chat_id = yt_chat_id_from_yt_channel[yt_channel]
                page_token = page_token_from_yt_chat_id[chat_id]
                if not yt_part.IsStreamAlive(yt_stream_id_from_yt_channel[yt_channel]):
                    continue
                print(f"YT_CHN2 {yt_channel}, {chat_id}, {page_token}")
                response = yt_part.GetMessages(chat_id, page_token)
                messages = response[0]
                page_token_from_yt_chat_id[chat_id] = response[1]
                for message in messages:
                    print(message[0], message[1])
                    messages_for_tw.put(MyMessage(tw_channel=tw_channel_from_yt_channel[yt_channel], yt_channel=yt_channel,
                                                  yt_stream_id=yt_stream_id_from_yt_channel[yt_channel], author=message[0],
                                                  text=message[1]))
            time.sleep(1)


    def tg_func():
        bot.polling(none_stop=True)


    tw_thread = threading.Thread(target=tw_func, daemon=False)
    yt_thread = threading.Thread(target=yt_func, daemon=False)
    tg_thread = threading.Thread(target=tg_func, daemon=False)

    tw_thread.start()
    yt_thread.start()
    tg_thread.start()

    tw_thread.join()
    yt_thread.join()
    tg_thread.join()
