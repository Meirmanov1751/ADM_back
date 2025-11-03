from rest_framework import serializers

from language.serializers import LanguageSerializer
from user.serializers import UserSerializer
from .models import News, NewsTranslation, NewsTag, Comment, VoteComment, Link, NewsCover, NewsFiles
from tags.serializers import TagSerializer
from quote.serializers import QuoteSerializer
from tags.models import Tag
from language.models import Language


class NewsTagSerializer(serializers.ModelSerializer):
    tag = TagSerializer(read_only=True)

    class Meta:
        model = NewsTag
        fields = ('tag',)


class NewsCoverSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewsCover
        fields = '__all__'


class NewsFileSerializer(serializers.ModelSerializer):


    class Meta:
        model = NewsFiles
        fields = '__all__'


class NewsTranslationSerializer(serializers.ModelSerializer):
    lang = LanguageSerializer(read_only=True)

    class Meta:
        model = NewsTranslation
        fields = '__all__'


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    user_id = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'comment', 'user_id', 'news', 'created_at']


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class NewsCoverCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewsCover
        fields = '__all__'

class NewsFilesCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewsFiles
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()
    covers = NewsCoverSerializer(many=True, required=False)
    files = NewsFileSerializer(many=True, required=False)
    comments = CommentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    quote = QuoteSerializer(read_only=True)
    author = UserSerializer(read_only=True)
    links = LinkSerializer(many=True, read_only=True)

    def get_translations(self, obj):
        request = self.context.get('request')
        print("Request context:", request)
        lang_id = request.query_params.get('lang_id')
        print("Lang ID:", lang_id)
        if lang_id:
            # Фильтровать переводы по lang_id, если параметр присутствует
            translations = obj.translations.filter(lang=lang_id)
        else:
            # Возвращать все переводы, если lang_id не указан
            translations = obj.translations.all()
        return NewsTranslationSerializer(translations, many=True).data

    class Meta:
        model = News
        fields = '__all__'


# class NewsCreateSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = News
#         fields = ['author', 'id','image', 'category','subcategory','exclusive','is_published' ]

class NewsTranslationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsTranslation
        fields = ['lang', 'title', 'text']


class NewsTagCreateSerializer(serializers.ModelSerializer):
    tag = serializers.IntegerField()

    class Meta:
        model = NewsTag
        fields = ['tag']


class LinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = [
            'facebook', 'whatsapp', 'telegram', 'vk',
            'twitter', 'threads', 'instagram', 'linkedin',
            'youtube', 'tiktok'
        ]


class NewsCreateSerializer(serializers.ModelSerializer):
    translations = NewsTranslationCreateSerializer(many=True, required=False)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    links = LinkCreateSerializer(many=True, required=False)
    covers = NewsCoverCreateSerializer(many=True, required=False)
    files = NewsFilesCreateSerializer(many=True, required=False)

    class Meta:
        model = News
        fields = [
            'id', 'author', 'image', 'category',
            'exclusive', 'is_published', 'quote', "announcement",
            'translations', 'tags', 'links', 'published_at', 'covers', 'files','link_to_source'
        ]

    def create(self, validated_data):
        translations_data = validated_data.pop('translations', [])
        covers_data = validated_data.pop('covers', [])
        files_data = validated_data.pop('files', [])
        tags_data = validated_data.pop('tags', [])
        links_data = validated_data.pop('links', [])

        news_instance = News.objects.create(**validated_data)

        for translation_data in translations_data:
            NewsTranslation.objects.create(news=news_instance, **translation_data)

        for file_data in files_data:
            NewsFiles.objects.create(news=news_instance, **file_data)

        for cover_data in covers_data:
            NewsCover.objects.create(news=news_instance, **cover_data)

        news_instance.tags.set(tags_data)

        for link_data in links_data:
            Link.objects.create(news=news_instance, **link_data)

        return news_instance

    def update(self, instance, validated_data):
        # Обновление существующих данных
        translations_data = validated_data.pop('translations', [])
        covers_data = validated_data.pop('covers', [])
        files_data = validated_data.pop('files', [])
        tags_data = validated_data.pop('tags', [])
        links_data = validated_data.pop('links', [])

        # Обновление полей News
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновление переводов
        instance.covers.all().delete()  # Удаляем старые переводы
        for cover_data in covers_data:
            NewsCover.objects.create(news=instance, **cover_data)

        instance.files.all().delete()
        for file_data in files_data:
            NewsFiles.objects.create(news=instance, **file_data)

        instance.translations.all().delete()  # Удаляем старые переводы
        for translation_data in translations_data:
            NewsTranslation.objects.create(news=instance, **translation_data)

        # Обновление тегов
        instance.tags.set(tags_data)

        # Обновление ссылок
        instance.links.all().delete()  # Удаляем старые ссылки
        for link_data in links_data:
            Link.objects.create(news=instance, **link_data)

        return instance


class NewsShortSerializer(serializers.ModelSerializer):
    translations = NewsTranslationSerializer(many=True, read_only=True)
    covers = NewsCoverSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)


    class Meta:
        model = News
        fields = ['id', 'covers', 'announcement', 'author', 'published_at', 'translations', 'category', 'image', 'created_at',
                  'updated_at']


class VoteCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = VoteComment
        fields = '__all__'
