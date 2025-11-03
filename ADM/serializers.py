from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Request, ASCCover, ASCFiles, RequestHistory, RequestRating,
    RequestCategory, Region, City, UserGroup
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()
# =========================
# Сериализаторы вспомогательных моделей
# =========================

class RequestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestCategory
        fields = ['id', 'code', 'name']

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']

class CitySerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'region']

class ASCCoverCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASCCover
        fields = '__all__'

class ASCFilesCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASCFiles
        fields = '__all__'

class RequestHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RequestHistory
        fields = ['id', 'user', 'user_name', 'action', 'timestamp', 'details','comment']

class RequestRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestRating
        fields = ['id', 'rating', 'comment', 'created_at']
class UserShortSerializer(serializers.ModelSerializer):
    region = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone_number", "region", "city"]

    def get_region(self, obj):
        # возвращает первый регион из групп пользователя (если есть)
        first_group = obj.groups.first()
        if first_group and first_group.regions.exists():
            return first_group.regions.first().name
        return None

    def get_city(self, obj):
        first_group = obj.groups.first()
        if first_group and first_group.cities.exists():
            return first_group.cities.first().name
        return None


class UserGroupSerializer(serializers.ModelSerializer):
    regions = serializers.StringRelatedField(many=True)
    cities = serializers.StringRelatedField(many=True)
    categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = UserGroup
        fields = ["id", "name", "regions", "cities", "categories"]

class ASCCoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASCCover
        fields = ["id", "cover", "order", "source_url", "alt"]


class ASCFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASCFiles
        fields = ["id", "title", "file"]

class RequestHistoryInfoSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = RequestHistory
        fields = ['id', 'user','action', 'timestamp', 'details','comment']
# =========================
# Основной сериализатор Request
# =========================
class RequestInfoSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    signatory = UserShortSerializer(read_only=True)
    executor = UserShortSerializer(read_only=True)
    moderator_group = UserGroupSerializer(read_only=True)

    covers = ASCCoverSerializer(many=True, read_only=True)
    files = ASCFilesSerializer(many=True, read_only=True)
    history = RequestHistoryInfoSerializer(many=True, read_only=True)
    rating = RequestRatingSerializer(read_only=True)

    region = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Request
        fields = [
            "id", "description", "category", "region", "city",
            "address", "contact_number", "status",
            "created_at", "updated_at",
            "user", "signatory", "executor", "moderator_group",
            "covers", "files", "history", "rating",
        ]

class RequestSerializer(serializers.ModelSerializer):
    group_moderator_ids = serializers.SerializerMethodField()
    covers = ASCCoverCreateSerializer(many=True, required=False, allow_null=True)
    files = ASCFilesCreateSerializer(many=True, required=False, allow_null=True)
    history = RequestHistorySerializer(many=True, read_only=True)
    rating = RequestRatingSerializer(read_only=True, required=False)

    # ForeignKey поля
    category = serializers.PrimaryKeyRelatedField(queryset=RequestCategory.objects.all())
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())

    class Meta:
        model = Request
        fields = '__all__'

    def validate(self, data):
        logger.debug(f"Validating data: {data}")
        required_fields = [ 'description', 'region', 'city', 'user', 'signatory']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: f"Поле '{field}' обязательно."})
        return data

    def create(self, validated_data):
        covers_data = validated_data.pop('covers', [])
        files_data = validated_data.pop('files', [])

        logger.debug(f"Creating Request with data: {validated_data}")
        request = Request.objects.create(**validated_data)

        RequestHistory.objects.create(
            request=request,
            user=validated_data['user'],
            action='created'
        )

        for cover_data in covers_data:
            ASCCover.objects.create(ASC=request, **cover_data)

        for file_data in files_data:
            ASCFiles.objects.create(ASC=request, **file_data)

        return request

    def update(self, instance, validated_data):
        covers_data = validated_data.pop('covers', [])
        files_data = validated_data.pop('files', [])

        instance = super().update(instance, validated_data)

        instance.covers.all().delete()
        for cover_data in covers_data:
            ASCCover.objects.create(ASC=instance, **cover_data)

        instance.files.all().delete()
        for file_data in files_data:
            ASCFiles.objects.create(ASC=instance, **file_data)

        return instance

    def get_group_moderator_ids(self, obj):
        if obj.moderator_group:
            return list(obj.moderator_group.users.values_list('id', flat=True))
        return []
