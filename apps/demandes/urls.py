from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DemandeViewSet

router = DefaultRouter()
router.register(r'demandes', DemandeViewSet, basename='demande')

urlpatterns = [
    path('', include(router.urls)),

    # Actions spécifiques
    path(
        'demandes/<int:pk>/assigner/',
        DemandeViewSet.as_view({'post': 'assigner_notaire'}),
        name='demande-assigner-notaire'
    ),
    path(
        'demandes/<int:pk>/completer/',
        DemandeViewSet.as_view({'post': 'completer_traitement'}),
        name='demande-completer-traitement'
    ),
]
