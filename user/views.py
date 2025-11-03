import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, ConfirmCodeSerializer
import random
from django.conf import settings
from twilio.rest import Client
import requests
from .serializers import UserSerializer
from djoser.views import UserViewSet
from rest_framework import filters

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    filter_backends = [filters.SearchFilter]
    search_fields = ['login', 'email', 'first_name', 'last_name', 'iin', 'phone_number']

    def get_serializer_class(self):
        return UserSerializer


class AdLoginView(APIView):
    """
    Авторизация через Active Directory
    """

    def post(self, request, *args, **kwargs):
        login = request.data.get("login")
        password = request.data.get("password")

        if not login or not password:
            return Response({"detail": "Введите логин и пароль"}, status=status.HTTP_400_BAD_REQUEST)
        BASE_URL = "http://10.8.27.97:8056/api/active-directory/1.0.12/"
        # Базовый URL АД (обрежем лишние / если есть)
        base_url = BASE_URL.rstrip("/")

        # Форматы логинов, которые будем проверять
        login_variants = [
            login,  # просто Kasymov.Dlt
            f"TELECOM\\{login}",  # DOMAIN\username
            f"{login}@telecom.kz",  # username@telecom.kz
        ]

        success = False
        ad_response = None
        final_login = None

        for variant in login_variants:
            try:
                url = f"{base_url}/account/{variant}/authorization"
                resp = requests.post(url, json={"password": password}, timeout=5)

                if resp.status_code == 200:
                    success = True
                    ad_response = resp.json()
                    final_login = variant
                    break
            except requests.RequestException as e:
                continue

        if not success:
            return Response({"detail": "Неверный логин или пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        # Создаём или берём пользователя
        email = f"{login}@telecom.kz"  # у нас email уникален
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": login,
                "is_active": True,
            }
        )

        # Генерим JWT токены
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "ad_login": final_login,
            }
        })


class CurrentUserView(APIView):

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


User = get_user_model()
logger = logging.getLogger('registration')


class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            confirmation_code = ''.join(random.choices('0123456789', k=4))
            user.confirmation_code = confirmation_code
            user.save()
            send_confirmation_code(user.phone_number, confirmation_code)
            logger.info(f'New user registered: {user.first_name} (phone: {user.phone_number})')
            return Response({'detail': 'User registered. Confirmation code sent.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_confirmation_code(phone_number, confirmation_code):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone_number = settings.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f'Ваш код подтверждения: {confirmation_code}',
        from_=twilio_phone_number,
        to=phone_number
    )

    return message.sid


class ConfirmCodeView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ConfirmCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            confirmation_code = serializer.validated_data['confirmation_code']
            try:
                user = User.objects.get(phone_number=phone_number, confirmation_code=confirmation_code)
                user.is_active = True
                user.is_staff = True
                user.confirmation_code = ''
                user.save()
                logger.info(f'User confirmed: {user.first_name} (phone: {user.phone_number})')
                return Response({'detail': 'Account confirmed.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'detail': 'Invalid code or phone number.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
