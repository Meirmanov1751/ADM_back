import django_filters
from django_filters import rest_framework as filters
from .models import Quote


class QuoteFilter(filters.FilterSet):
    class Meta:
        model = Quote
        fields = '__all__'
