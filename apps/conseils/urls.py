from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConseilsViewSet

router = DefaultRouter()
router.register(r'conseils', ConseilsViewSet, basename='conseil')

urlpatterns = [
    path('', include(router.urls)),
]
