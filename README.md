# Coursework

~~Проект нативного мультичата для стриминговых платформ за счёт пересылки сообщений между чатами с помощью ботов~~

В царстве потокового эфира возрождается изящный мост, объединяющий изолированные чаты разных платформ. Нативная система мультичата дирижирует симфонией общения, где сообщения порхают между виртуальными залами, поддерживая нить диалога. Посредством виртуозной работы ботов-вестников перебрасывается вербальный мост, стирая границы и позволяя разговорам свободно течь сквозь цифровые пространства. **Powered by chatgpt**

## Зависимости

[telebot](https://pypi.org/project/pyTelegramBotAPI/), [twitchio](https://twitchio.dev/en/latest/installing.html), google_api: [1](https://github.com/googleapis/google-api-python-client), [2](https://pypi.org/project/google-auth-oauthlib/), [3](https://pypi.org/project/google-auth/)

### Подготовка

1. Создайте .env файл в директории проекта
2. YouTube:
    1. Создайте проект в [Консоль разработчика гугл](https://console.cloud.google.com/apis/dashboard)
    2. Включите YouTube Data API v3
    3. На вкладке Credentials создайте новый индификатор Oauth, и сохраните client_secret.json в директорию с проектом
    4. Сохраните в .env  индификатор аккаунта (индификатор канала), который будет использоваться как бот для пересылки в переменную YT_BOT_ID.
3. Twitch:
    1. Подготовка к запуску описана на [TwitchIO Quickstart](https://twitchio.dev/en/latest/quickstart.html)
    2. Сохраните полученный токен в .env в переменную TWITCH_TOKEN.
4. Telegram:
    1. Создайте нового бота через [BotFather](https://t.me/BotFather) и получите токен тг бота.
    2. Сохраните полученный токен в .env в переменную TG_TOKEN.

  Просто запустите main.py ;)
