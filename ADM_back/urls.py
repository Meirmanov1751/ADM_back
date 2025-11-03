from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView,
)

from AI.views import ChatBotLView, ChatBotAView, KnowledgeBaseUploadView
from language.urls import router as post_language
from news.urls import router as post_news
from tags.urls import router as post_tags
from quote.urls import router as post_quote
from ADM.urls import router as post_ADM
from repair_status.urls import router as post_repair_status
from user.urls import router as user

router = DefaultRouter()

router.registry.extend(post_language.registry)
router.registry.extend(post_news.registry)
router.registry.extend(post_tags.registry)
router.registry.extend(post_quote.registry)
router.registry.extend(post_ADM.registry)
router.registry.extend(post_repair_status.registry)
router.registry.extend(user.registry)


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
    path("", include("user.urls")),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('chatL/', ChatBotLView.as_view(), name='chatbotL'),
    path('chatA/', ChatBotAView.as_view(), name='chatbotA'),
    path('upload/', KnowledgeBaseUploadView.as_view(), name='upload-document'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
