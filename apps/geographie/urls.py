from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, VilleViewSet

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'villes', VilleViewSet, basename='ville')
urlpatterns = [
    path('', include(router.urls)),
]