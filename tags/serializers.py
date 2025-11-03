from rest_framework import serializers

from language.serializers import LanguageSerializer
from .models import Tag, TagTranslation


class TagTranslationSerializer(serializers.ModelSerializer):
    lang = LanguageSerializer(read_only=True)

    class Meta:
        model = TagTranslation
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    translations = TagTranslationSerializer(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = '__all__'


class TagTranslationCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TagTranslation
        fields = ['tag', 'lang']


# Сериализатор для тега
class TagCreateSerializer(serializers.ModelSerializer):
    translations = TagTranslationCreateSerializer(many=True, required=False)

    class Meta:
        model = Tag
        fields = ['id', 'tag_name', 'translations']

    def create(self, validated_data):
        translations_data = validated_data.pop('translations', [])

        # Создание объекта Tag
        tag_instance = Tag.objects.create(**validated_data)

        # Создание переводов для Tag
        for translation_data in translations_data:
            TagTranslation.objects.create(tag_id=tag_instance, **translation_data)

        return tag_instance