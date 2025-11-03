from rest_framework.routers import DefaultRouter
from .views import TagViewSet, TagTranslationViewSet, TagCreateViewSet

router = DefaultRouter()

router.register('tags_create', TagCreateViewSet, basename='tags_create')

router.register(r'tags', TagViewSet)
router.register(r'tags_translation', TagTranslationViewSet)
