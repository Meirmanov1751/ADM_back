from django.urls import path
from .views import UserRegistrationView, ConfirmCodeView, AdLoginView
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    path("auth/ad-login/", AdLoginView.as_view(), name="ad-login"),
    path('auth/register/', UserRegistrationView.as_view(), name='user-registration'),
    path('auth/confirm_code/', ConfirmCodeView.as_view(), name='confirm-code'),
]