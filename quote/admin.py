from django.contrib import admin
from .models import (
    Quote, QuoteTranslation,
)


class QuoteTranslationInline(admin.TabularInline):  # Или `admin.StackedInline` в зависимости от вашего предпочтения
    model = QuoteTranslation
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('id',)
    inlines = [QuoteTranslationInline]
