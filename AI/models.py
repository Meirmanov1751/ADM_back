from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    message = models.TextField()
    response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



class KnowledgeBase(models.Model):
    CATEGORY_CHOICES = [
        ('law', 'Юридическая база'),
        ('accounting', 'Бухгалтерская база'),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    file = models.FileField(upload_to='knowledge_base/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
