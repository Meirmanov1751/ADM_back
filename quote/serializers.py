from rest_framework import serializers

from language.serializers import LanguageSerializer
from .models import Quote, QuoteTranslation


class QuoteTranslationSerializer(serializers.ModelSerializer):
    lang = LanguageSerializer(read_only=True)

    class Meta:
        model = QuoteTranslation
        fields = '__all__'


class QuoteSerializer(serializers.ModelSerializer):
    translations = QuoteTranslationSerializer(many=True, read_only=True)

    class Meta:
        model = Quote
        fields = '__all__'

class QuoteTranslationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteTranslation
        fields = ['quote', 'lang']  # Убедитесь, что здесь нет 'quote_id'


class QuoteCreateSerializer(serializers.ModelSerializer):
    translations = QuoteTranslationCreateSerializer(many=True, required=False)

    class Meta:
        model = Quote
        fields = ['id', 'quote_author', 'translations']

    def create(self, validated_data):
        translations_data = validated_data.pop('translations', [])

        # Создание экземпляра Quote
        quote_instance = Quote.objects.create(**validated_data)

        # Создание переводов для цитаты
        for translation_data in translations_data:
            QuoteTranslation.objects.create(quote_id=quote_instance, **translation_data)

        return quote_instance