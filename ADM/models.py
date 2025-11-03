from django.db import models
from user.models import User
from django.db import models
from user.models import User


# Категории
class RequestCategory(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


# Регионы
class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Города (привязаны к региону)
class City(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return f"{self.name} ({self.region.name})"



STATUS_CHOICES = [
    ('pending', 'Ожидает подписи'),
    ('signed', 'Подписана'),
    ('under_review', 'На рассмотрении'),
    ('approved', 'Одобрена модератором'),
    ('assigned', 'Назначена исполнителю'),
    ('in_progress', 'В процессе'),
    ('completed', 'Выполнена'),
    ('rejected', 'Отклонена'),
]


# Главная заявка
class Request(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_requests')
    signatory = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signed_requests')
    moderator_group = models.ForeignKey('UserGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')

    executor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                 related_name='executed_requests')

    category = models.ForeignKey(RequestCategory, on_delete=models.SET_NULL, null=True, related_name='requests')
    description = models.TextField()

    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, related_name='requests')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='requests')

    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    image = models.ImageField(upload_to='requests/', blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - {self.status}"

    def __str__(self):
        return f"{self.description} - {self.status}"

class ASCCover(models.Model):
    ASC = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='covers')
    cover = models.ImageField(upload_to='ADM/covers/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    source_url = models.TextField(blank=True, null=True)
    alt = models.CharField(max_length=255, blank=True, null=True)

class ASCFiles(models.Model):
    ASC = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='ADM/', blank=True, null=True)

class RequestHistory(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    user_full_name = models.CharField(max_length=255, blank=True, null=True)
    related_user_full_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.request} - {self.action} by {self.user}"

class RequestRating(models.Model):
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name='rating')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for {self.request}"

# ✅ Группы с привязкой к существующим регионам, городам и категориям
class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    regions = models.ManyToManyField(Region, related_name='user_groups')
    cities = models.ManyToManyField(City, related_name='user_groups')
    categories = models.ManyToManyField(RequestCategory, related_name='user_groups')
    users = models.ManyToManyField(User, related_name='groups')

    def __str__(self):
        return self.name