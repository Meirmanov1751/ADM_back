from django.contrib import admin
from .models import (
    News, NewsTranslation,
    NewsTag, Link, Comment, VoteComment, Subscriber,
    NewsCover, NewsFiles
)

admin.site.register(Subscriber)
admin.site.register(Comment)
admin.site.register(VoteComment)


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1


class NewsTranslationInline(admin.StackedInline):
    model = NewsTranslation
    extra = 1

class NewsCoverInline(admin.StackedInline):
    model = NewsCover
    extra = 1

class NewsFilesInline(admin.StackedInline):
    model = NewsFiles
    extra = 1


class NewsTagInline(admin.TabularInline):  # Или `admin.StackedInline` в зависимости от вашего предпочтения
    model = NewsTag


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'author_id', 'quote', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author_id',)
    inlines = [NewsTranslationInline, NewsTagInline, LinkInline, NewsCoverInline, NewsFilesInline]
