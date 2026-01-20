from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet, InscriptionViewSet, evenement_choices

router = DefaultRouter()
router.register(r'evenements', EvenementViewSet, basename='evenement')
router.register(r'inscriptions', InscriptionViewSet, basename='inscription')

urlpatterns = [
    path('evenements/choices/', evenement_choices, name='evenement-choices'),
    path('', include(router.urls)),
]
