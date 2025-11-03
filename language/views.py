from django.shortcuts import render
from rest_framework import mixins, viewsets
from rest_framework import viewsets
from .serializers import LanguageSerializer
from .models import Language



class LanguageViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
