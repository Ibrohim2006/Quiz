import random
from datetime import timedelta
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings


def generate_code():
    return random.randint(100000, 999999)


def send_verification_email(user, code):
    subject = "Email Tasdiqlash"
    message = f"Sizning tasdiqlash kodingiz: {code}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def generate_expiry_time():
    return now() + timedelta(minutes=10)
