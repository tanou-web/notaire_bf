# apps/core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CoreConfigurationViewSet, CorePageViewSet

router = DefaultRouter()
router.register(r'configurations', CoreConfigurationViewSet, basename='configuration')
router.register(r'pages', CorePageViewSet, basename='page')

urlpatterns = [
    path('', include(router.urls)),
]

