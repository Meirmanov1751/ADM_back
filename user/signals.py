from django.conf import settings
from twilio.rest import Client
from djoser.signals import user_registered
from django.dispatch import receiver
import random


@receiver(user_registered)
def handle_user_registered(sender, user, request, **kwargs):
    profile = user
    if profile:
        if profile.role == 'guest':
            confirmation_code = ''.join(random.choices('0123456789', k=4))
            profile.confirmation_code = confirmation_code
            profile.is_active = False  # Пользователь не активен до подтверждения
            profile.save()
            send_confirmation_code(profile.phone_number, confirmation_code)
        else:
            profile.is_active = True
            profile.is_staff = True


def send_confirmation_code(phone_number, confirmation_code):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone_number = settings.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f'Ваш код подтверждения: {confirmation_code}',
        from_=twilio_phone_number,
        to=phone_number
    )

    return message.sid
