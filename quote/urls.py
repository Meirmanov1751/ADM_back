from rest_framework.routers import DefaultRouter
from .views import QuoteViewSet, QuoteTranslationViewSet, QuoteCreateViewSet

router = DefaultRouter()

router.register('quote_create', QuoteCreateViewSet, basename='quote_create')
router.register('quote', QuoteViewSet)
router.register(r'quote_translation', QuoteTranslationViewSet)
