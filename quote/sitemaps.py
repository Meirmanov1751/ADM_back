from django.contrib.sitemaps import Sitemap
from .models import Quote


class QuoteSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.7

    def items(self):
        return Quote.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
