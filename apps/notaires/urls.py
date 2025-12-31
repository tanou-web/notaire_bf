# apps/notaires/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    NotaireViewSet,
    NotaireStatsAPIView,
    CotisationViewSet,
    RechercheNotairesAPIView
)

router = DefaultRouter()

# Ressources principales
router.register(r'notaires', NotaireViewSet, basename='notaire')
router.register(r'cotisations', CotisationViewSet, basename='cotisation')

urlpatterns = [
    # Routes REST standards (ViewSets)
    path('', include(router.urls)),

    #  Statistiques globales (admin)
    path(
        'notaires/stats/',
        NotaireStatsAPIView.as_view(),
        name='notaires-stats'
    ),

    #  Recherche avancée de notaires
    path(
        'notaires/recherche/',
        RechercheNotairesAPIView.as_view(),
        name='notaires-recherche'
    ),
]
