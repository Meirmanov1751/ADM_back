# from celery import shared_task
# from django.core.mail import send_mail
#
# from news.models import News
# from .models import Subscriber
#
# @shared_task
# def send_new_post_notification(news_id):
#     subscribers = Subscriber.objects.all()
#     emails = [subscriber.email for subscriber in subscribers]
#     post = News.objects.get(id=news_id)
#
#     subject = f'New Post: {post.title}'
#     message = f'Check out our new post: {post.title}\n\n{post.content}'
#     send_mail(subject, message, 'your_email@example.com', emails)