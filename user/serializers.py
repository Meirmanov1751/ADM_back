from djoser.serializers import TokenSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from news.models import News
from django.db.models import Sum

from user.models import Position, Organization, Department

User = get_user_model()

from ADM.models import UserGroup


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ['id', 'name']


class UserPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'name']


class UserOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name']


class UserDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'phone_number', 'first_name', 'last_name', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role'],
        )
        user.set_password(validated_data['password'])
        user.is_active = True
        user.is_staff = True
        user.save()
        return user


class ConfirmCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    confirmation_code = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    groups = UserGroupSerializer(many=True, read_only=True)
    position = UserPositionSerializer(read_only=True)
    organization = UserOrganizationSerializer(read_only=True)
    department = UserDepartmentSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'middle_name', 'login', 'iin', 'birth_date', 'department',
            'phone_number', 'role',
            'avatar', 'is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'position', 'organization'
        ]
