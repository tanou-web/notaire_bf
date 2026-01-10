from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'paiements'

router = DefaultRouter()
from .views import PaiementViewSet, PaiementWebhookAPIView

router.register(r'transactions', PaiementViewSet, basename='paiement')

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints d'intégration avec les opérateurs
    path('initier-paiement/', views.InitierPaiementView.as_view(), name='initier-paiement'),
    path('verifier-paiement/', views.VerifierPaiementView.as_view(), name='verifier-paiement'),
    path('callback/', views.CallbackView.as_view(), name='callback'),
    
    # Webhooks pour les opérateurs
    path('webhook/orange_money/', views.WebhookView.as_view(), name='webhook-orange-money'),
    path('webhook/moov_money/', views.WebhookView.as_view(), name='webhook-moov-money'),
    path('webhook/', PaiementWebhookAPIView.as_view(), name='paiement-webhook'),

    # Export et rapports
    path('export/rapport/', views.ExportRapportView.as_view(), name='export-rapport'),
]