from django.db import models
from django.urls import reverse
from language.models import Language


# Create your models here.
class Quote(models.Model):
    quote_author = models.CharField(max_length=255)

    def __str__(self):
        return f"Цитата {self.quote_author}"

    def get_absolute_url(self):
        return reverse('quote-detail', args=[str(self.id)])

    class Meta:
        ordering = ["id"]
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"


class QuoteTranslation(models.Model):
    quote = models.TextField()
    lang = models.ForeignKey(Language, on_delete=models.CASCADE)
    quote_id = models.ForeignKey(Quote, related_name='translations', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('quote_id', 'lang')
        ordering = ["id"]
        verbose_name = "Перевод цитаты"
        verbose_name_plural = "Переводы цитат"

    def __str__(self):
        return f"Цитата {self.quote_id.id} ({self.lang})"
