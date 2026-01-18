from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet, InscriptionViewSet

router = DefaultRouter()
router.register(r'evenements', EvenementViewSet, basename='evenement')
router.register(r'inscriptions', InscriptionViewSet, basename='inscription')

urlpatterns = [
    path('', include(router.urls)),
]
