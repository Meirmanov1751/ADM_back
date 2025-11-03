from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import News
from .utils import notify_subscribers


@receiver(post_save, sender=News)
def post_save_handler(sender, instance, created, **kwargs):
    print("рассылка")
    if created:
        notify_subscribers(instance)
