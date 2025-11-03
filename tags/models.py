from django.db import models
from language.models import Language


# Create your models here.
class Tag(models.Model):
    tag_name = models.CharField(max_length=255)

    def __str__(self):
        return self.tag_name


class TagTranslation(models.Model):
    tag = models.CharField(max_length=255)
    lang = models.ForeignKey(Language, on_delete=models.CASCADE)
    tag_id = models.ForeignKey(Tag, related_name='translations', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('tag_id', 'lang')

    def __str__(self):
        return f"Тег {self.tag_id.id} ({self.lang})"
