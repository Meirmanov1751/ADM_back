from django.shortcuts import render
from rest_framework import mixins, viewsets
from rest_framework import viewsets
from .models import Quote, QuoteTranslation
from django_filters.rest_framework import DjangoFilterBackend
from .filters import QuoteFilter
from .serializers import QuoteSerializer, QuoteTranslationSerializer, QuoteCreateSerializer

class QuoteCreateViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Quote.objects.all()
    serializer_class = QuoteCreateSerializer

class QuoteViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = QuoteFilter


class QuoteTranslationViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = QuoteTranslation.objects.all()
    serializer_class = QuoteTranslationSerializer
