from django.contrib.sitemaps import Sitemap
from .models import News, Comment


class NewsSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return News.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CommentSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Comment.objects.all()
