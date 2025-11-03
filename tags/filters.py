# filters.py
import django_filters
from django_filters import rest_framework as filters
from .models import Tag


class TagFilter(filters.FilterSet):
    class Meta:
        model = Tag
        fields = '__all__'
