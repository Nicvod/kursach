import telebot
from telebot import types
from extentions import HostsUnion, ThreadCommunication

from db_part import DbClass


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


class MyTgBot:
    def __init__(self, token, communicator: ThreadCommunication, acc_db: DbClass):
        self.bot = telebot.TeleBot(token)
        self.communicator = communicator
        self.acc_db = acc_db
        self.id_form_tg_id = dict()
        self.cur_livestreams = set()
        self.setup_handlers()

    def GetUserId(self, tg_id):
        if not (tg_id in self.id_form_tg_id):
            usr_id = self.acc_db.GetIdFromUsr(tg_id)[0]
            self.id_form_tg_id[tg_id] = usr_id
        return self.id_form_tg_id[tg_id]

    def TwitchReg(self, message):
        usr_id = self.GetUserId(message.from_user.id)
        self.acc_db.ChangeTwAcc(usr_id, message.text)
        self.bot.send_message(message.chat.id, 'Твич аккаунт успешно привязан, что будем делать дальше?',
                              reply_markup=MakeStartKeyBoard())

    def YouTubeReg(self, message):
        usr_id = self.GetUserId(message.from_user.id)
        self.acc_db.ChangeYtAcc(usr_id, message.text)
        self.bot.send_message(message.chat.id, 'Ютуб аккаунт успешно привязан, что будем делать дальше?',
                              reply_markup=MakeStartKeyBoard())

    def TwitchAdd(self, call):
        usr_id = self.GetUserId(call.from_user.id)
        tw_acc = self.acc_db.GetTwAcc(usr_id)[0]
        if tw_acc is not None:
            # Checking that the account has already been added
            markup = types.InlineKeyboardMarkup()
            yes_btn = types.InlineKeyboardButton('Да', callback_data='tw_confirm')
            markup.add(yes_btn)
            bst_btn = types.InlineKeyboardButton('Нет', callback_data='back_to_start')
            markup.add(bst_btn)
            self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       text=f'Вы уже прикрепляли аккаунт: {tw_acc}, хотите его изменить?',
                                       reply_markup=markup)
        else:
            self.bot.send_message(chat_id=call.message.chat.id, text="Введите название твич аккаунта")
            self.bot.register_next_step_handler(call.message, self.TwitchReg)

    def YouTubeAdd(self, call):
        usr_id = self.GetUserId(call.from_user.id)
        yt_acc = self.acc_db.GetYtAcc(usr_id)[0]

        if yt_acc is not None:
            # Checking that the account has already been added
            markup = types.InlineKeyboardMarkup()
            yes_btn = types.InlineKeyboardButton('Да', callback_data='yt_confirm')
            markup.add(yes_btn)
            bst_btn = types.InlineKeyboardButton('Нет', callback_data='back_to_start')
            markup.add(bst_btn)
            self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       text=f'Вы уже прикрепляли аккаунт: {yt_acc}, хотите его изменить?',
                                       reply_markup=markup)
        else:
            self.bot.send_message(chat_id=call.message.chat.id, text="Введите индификатор стрима "
                                                                     "Пример индификатора: "
                                                                     "https://www.youtube.com/watch?v=B-LED-y7Gko"
                                                                     "/B-LED-y7Gko\n"
                                                                     "<pre>B-LED-y7Gko</pre>",
                                  parse_mode='HTML')
            self.bot.register_next_step_handler(call.message, self.YouTubeReg)

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def Start(message):
            self.bot.send_message(message.chat.id, 'Что хотите сделать?', reply_markup=MakeStartKeyBoard())

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            if call.data == 'TW_reg':
                self.TwitchAdd(call)
            elif call.data == 'YT_reg':
                self.YouTubeAdd(call)
            elif call.data == 'back_to_start':
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           text='Что хотите сделать?', reply_markup=MakeStartKeyBoard())
            elif call.data == "tw_confirm":
                self.bot.send_message(chat_id=call.message.chat.id, text="Введите название твич аккаунта")
                self.bot.register_next_step_handler(call.message, self.TwitchReg)
            elif call.data == "yt_confirm":
                self.bot.send_message(chat_id=call.message.chat.id, text="Введите индификатор стрима "
                                                                         "Пример индификатора: "
                                                                         "https://www.youtube.com/watch?v=B-LED-y7Gko"
                                                                         "/B-LED-y7Gko\n"
                                                                         "<pre>B-LED-y7Gko</pre>",
                                      parse_mode='HTML')
                self.bot.register_next_step_handler(call.message, self.YouTubeReg)
            elif call.data == "start_livestream":
                usr_id = self.GetUserId(call.from_user.id)
                tw_acc = self.acc_db.GetTwAcc(usr_id)[0]
                yt_acc = self.acc_db.GetYtAcc(usr_id)[0]
                if tw_acc is None or yt_acc is None:
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                               text="Не все аккаунты ещё привязаны", reply_markup=MakeStartKeyBoard())
                elif call.from_user.id in self.cur_livestreams:
                    if call.message.text != "Вы уже начали пересылку сообщений":
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   text="Вы уже начали пересылку сообщений",
                                                   reply_markup=MakeStartKeyBoard())
                else:
                    if call.message.text != "Пересылка сообщений начата":
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   text="Пересылка сообщений начата", reply_markup=MakeStartKeyBoard())
                        self.cur_livestreams.add(call.from_user.id)
                        self.communicator.add_hosts_info(thread_name="TW_CNG",
                                                         item=HostsUnion(tw_info=tw_acc, yt_info=yt_acc, status=True))
                        self.communicator.add_hosts_info(thread_name="YT_CNG",
                                                         item=HostsUnion(tw_info=tw_acc, yt_info=yt_acc, status=True))
            elif call.data == "stop_livestream":
                usr_id = self.GetUserId(call.from_user.id)
                tw_acc = self.acc_db.GetTwAcc(usr_id)[0]
                yt_acc = self.acc_db.GetYtAcc(usr_id)[0]
                if call.from_user.id not in self.cur_livestreams:
                    if call.message.text != "Вы не начинали пересылку сообщений":
                        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                              text="Вы не начинали пересылку сообщений",
                                              reply_markup=MakeStartKeyBoard())
                else:
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text="Пересылка сообщений прекращена", reply_markup=MakeStartKeyBoard())
                    self.cur_livestreams.discard(call.from_user.id)
                    self.communicator.add_hosts_info(thread_name="TW_CNG",
                                                     item=HostsUnion(tw_info=tw_acc, yt_info=yt_acc, status=False))
                    self.communicator.add_hosts_info(thread_name="YT_CNG",
                                                     item=HostsUnion(tw_info=tw_acc, yt_info=yt_acc, status=False))
            elif call.data == "help":
                usr_id = self.GetUserId(call.from_user.id)
                tw_acc = self.acc_db.GetTwAcc(usr_id)[0]
                yt_acc = self.acc_db.GetYtAcc(usr_id)[0]
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
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                           text=bot_message, reply_markup=markup)

    def run(self):
        self.bot.polling(none_stop=True)
