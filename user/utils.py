from django.conf import settings
from twilio.rest import Client
from django.http import HttpResponse

def send_confirmation_code(phone_number, confirmation_code):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone_number = settings.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            body=f'Your confirmation code: {confirmation_code}',
            from_=twilio_phone_number,
            to=phone_number
        )
        return HttpResponse(f'SMS sent to {phone_number} successfully!')
    except Exception as e:
        return HttpResponse(f'Failed to send SMS: {str(e)}')