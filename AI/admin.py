from django.contrib import admin

from .models import ChatMessage, KnowledgeBase

# Register your models here.
admin.site.register(ChatMessage)
admin.site.register(KnowledgeBase)
