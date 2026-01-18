# apps/ventes/urls.py - AVEC ROUTER (OPTIONNEL)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'stickers', views.VentesStickerViewSet, basename='sticker')
router.register(r'references-stickers', views.ReferenceStickerViewSet, basename='reference-sticker')
router.register(r'ventes-stickers-notaires', views.VenteStickerNotaireViewSet, basename='vente-sticker-notaire')

urlpatterns = [
    # URLs du router
    path('', include(router.urls)),
    
    # URLs d'actions personnalisées
    path('ventes-stickers/creer/', views.VenteStickerViewSet.as_view({'post': 'creer'}), name='creer-vente-sticker'),
    path('ventes-stickers/par-notaire/', views.VenteStickerViewSet.as_view({'get': 'par_notaire'}), name='ventes-par-notaire'),
    path('demandes/creer/', views.DemandeViewSet.as_view({'post': 'creer'}), name='creer-demande'),
    path('paiements/initier/', views.PaiementViewSet.as_view({'post': 'initier'}), name='initier-paiement'),
    path('statistiques/notaires/', views.StatistiquesNotairesAPIView.as_view(), name='statistiques-notaires'),
]