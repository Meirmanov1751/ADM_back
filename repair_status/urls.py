from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RepairViewSet, RepairTaskViewSet

router = DefaultRouter()
router.register(r'repairs', RepairViewSet, basename='repair')  # Explicitly set basename
router.register(r'tasks', RepairTaskViewSet, basename='task')  # Explicitly set basename