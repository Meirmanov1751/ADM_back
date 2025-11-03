from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, CommentViewSet, NewsShortViewSet, CommentCreateViewSet, NewsCreateViewSet, \
    NewsAdminViewSet

router = DefaultRouter()

router.register('news', NewsViewSet, basename='news')
router.register('news_create', NewsCreateViewSet, basename='news_create')
router.register('news_admin', NewsAdminViewSet, basename='NewsAdminViewSet')
router.register('news_short', NewsShortViewSet, basename='news_short')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'commentsCreate', CommentCreateViewSet, basename='commentsCreate')
