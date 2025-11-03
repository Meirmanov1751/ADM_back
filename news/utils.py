from django.core.mail import send_mail
from django.conf import settings
from .models import Subscriber


def notify_subscribers(news):
    try:
        print("notify_subscribers")
        subscribers = Subscriber.objects.all()
        subject = 'New Post Notification'
        message = f'Hi,\n\nA new post titled "{news.category}" has been published.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [subscriber.email for subscriber in subscribers]
        print(from_email)
        print(recipient_list)

        send_mail(subject, message, from_email, recipient_list)
    except:
        print("except")
