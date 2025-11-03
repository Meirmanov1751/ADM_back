from django.contrib import admin
from .models import (
    Tag, TagTranslation
)


class TagTranslationInline(admin.TabularInline):  # Или `admin.StackedInline` в зависимости от вашего предпочтения
    model = TagTranslation
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id',)
    inlines = [TagTranslationInline]
