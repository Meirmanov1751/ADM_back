from rest_framework.routers import DefaultRouter

from .views import RequestViewSet, CityViewSet, CategoryViewSet, RegionViewSet, RequestInfoViewSet

router = DefaultRouter()

router.register(r'ADM', RequestViewSet)
router.register(r'ADMinfo', RequestInfoViewSet, basename='ADMinfo')
router.register(r'cities', CityViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'categories', CategoryViewSet)
