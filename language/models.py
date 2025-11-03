from django.db import models


class Language(models.Model):
    lang = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.lang

    class Meta:
        ordering = ["id"]
        verbose_name = "Язык"
        verbose_name_plural = "Языки"
