import requests
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
TELEGRAM_API_URL = settings.TELEGRAM_API_URL
BOT_ID = settings.BOT_ID
CHAT_ID = settings.CHAT_ID


def send_message_telegram(obj):
    data = obj
    message = (f"Project:Test\n"
               f"phone_number:{data.get('user')}\n"
               f"message:{data.get('subject')}\n"
               f"score:{data.get('score')}\n"
               f"attempts:{data.get('attempts')}\n"
               f"start_time:{data.get('start_time')}\n"
               f"end_time:{data.get('end_time')}\n")
    return requests.get(TELEGRAM_API_URL.format(BOT_ID, message, CHAT_ID))


