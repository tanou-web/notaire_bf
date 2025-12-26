# apps/ventes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'stickers', views.VentesStickerViewSet, basename='sticker')
router.register(r'clients', views.ClientViewSet, basename='client')
router.register(r'demandes', views.DemandeViewSet, basename='demande')
router.register(r'factures', views.VentesFactureViewSet, basename='facture')
router.register(r'paiements', views.PaiementViewSet, basename='paiement')
router.register(r'paniers', views.PanierViewSet, basename='panier')
router.register(r'avis', views.AvisClientViewSet, basename='avis')
router.register(r'codes-promo', views.CodePromoViewSet, basename='code-promo')

urlpatterns = [
    # Routes du router (CRUD standard)
    path('', include(router.urls)),
    
    # ============ PUBLIC ============
    path('catalogue/', views.catalogue_stickers, name='catalogue'),
    path('sticker/<int:pk>/', views.detail_sticker, name='detail-sticker'),
    path('contact/', views.contact_commercial, name='contact-commercial'),
    path('stats/rapides/', views.stats_rapides, name='stats-rapides'),
    
    # ============ UTILISATEUR ============
    path('mon-compte/', views.mon_compte, name='mon-compte'),
    path('modifier-compte/', views.modifier_compte, name='modifier-compte'),
    
    # ============ ADMIN ============
    path('statistiques/', views.StatistiquesAPIView.as_view(), name='statistiques'),
    
    # ============ ACTIONS SPÉCIFIQUES ============
    # Stickers
    path('stickers/disponibles/', 
         views.VentesStickerViewSet.as_view({'get': 'disponibles'}), 
         name='stickers-disponibles'),
    path('stickers/en-rupture/', 
         views.VentesStickerViewSet.as_view({'get': 'en_rupture'}), 
         name='stickers-en-rupture'),
    path('stickers/populaires/', 
         views.VentesStickerViewSet.as_view({'get': 'populaires'}), 
         name='stickers-populaires'),
    path('stickers/nouveaux/', 
         views.VentesStickerViewSet.as_view({'get': 'nouveaux'}), 
         name='stickers-nouveaux'),
    path('stickers/par-categorie/', 
         views.VentesStickerViewSet.as_view({'get': 'par_categorie'}), 
         name='stickers-par-categorie'),
    path('stickers/<int:pk>/statistiques/', 
         views.VentesStickerViewSet.as_view({'get': 'statistiques'}), 
         name='sticker-statistiques'),
    path('stickers/<int:pk>/ajuster-stock/', 
         views.VentesStickerViewSet.as_view({'post': 'ajuster_stock'}), 
         name='ajuster-stock'),
    
    # Clients
    path('clients/recherche/', 
         views.ClientViewSet.as_view({'get': 'recherche'}), 
         name='clients-recherche'),
    path('clients/<int:pk>/demandes/', 
         views.ClientViewSet.as_view({'get': 'demandes'}), 
         name='client-demandes'),
    path('clients/<int:pk>/statistiques/', 
         views.ClientViewSet.as_view({'get': 'statistiques'}), 
         name='client-statistiques'),
    path('clients/<int:pk>/ajouter-points/', 
         views.ClientViewSet.as_view({'post': 'ajouter_points'}), 
         name='ajouter-points'),
    
    # Demandes
    path('demandes/suivi/', 
         views.DemandeViewSet.as_view({'get': 'suivi'}), 
         name='suivi-demandes'),
    path('demandes/<int:pk>/confirmer/', 
         views.DemandeViewSet.as_view({'post': 'confirmer'}), 
         name='confirmer-demande'),
    path('demandes/<int:pk>/expedier/', 
         views.DemandeViewSet.as_view({'post': 'expedier'}), 
         name='expedier-demande'),
    path('demandes/<int:pk>/ajouter-paiement/', 
         views.DemandeViewSet.as_view({'post': 'ajouter_paiement'}), 
         name='ajouter-paiement-demande'),
    
    # Paiements
    path('paiements/par-periode/', 
         views.PaiementViewSet.as_view({'get': 'par_periode'}), 
         name='paiements-par-periode'),
    
    # Panier
    path('paniers/<int:pk>/ajouter-item/', 
         views.PanierViewSet.as_view({'post': 'ajouter_item'}), 
         name='panier-ajouter-item'),
    path('paniers/<int:pk>/retirer-item/', 
         views.PanierViewSet.as_view({'post': 'retirer_item'}), 
         name='panier-retirer-item'),
    path('paniers/<int:pk>/vider/', 
         views.PanierViewSet.as_view({'post': 'vider'}), 
         name='panier-vider'),
    path('paniers/<int:pk>/passer-commande/', 
         views.PanierViewSet.as_view({'post': 'passer_commande'}), 
         name='panier-passer-commande'),
    
    # Factures
    path('factures/<int:pk>/emettre/', 
         views.VentesFactureViewSet.as_view({'post': 'emettre'}), 
         name='facture-emettre'),
    path('factures/<int:pk>/enregistrer-paiement/', 
         views.VentesFactureViewSet.as_view({'post': 'enregistrer_paiement'}), 
         name='facture-enregistrer-paiement'),
    
    # Avis
    path('avis/par-sticker/<int:sticker_id>/', 
         views.AvisClientViewSet.as_view({'get': 'par_sticker'}), 
         name='avis-par-sticker'),
    path('avis/mes-avis/', 
         views.AvisClientViewSet.as_view({'get': 'mes_avis'}), 
         name='mes-avis'),
    path('avis/<int:pk>/marquer-utile/', 
         views.AvisClientViewSet.as_view({'post': 'marquer_utile'}), 
         name='avis-marquer-utile'),
    path('avis/<int:pk>/marquer-inutile/', 
         views.AvisClientViewSet.as_view({'post': 'marquer_inutile'}), 
         name='avis-marquer-inutile'),
    
    # Codes promo
    path('codes-promo/verifier/', 
         views.CodePromoViewSet.as_view({'post': 'verifier'}), 
         name='verifier-code-promo'),
    path('codes-promo/<int:pk>/utiliser/', 
         views.CodePromoViewSet.as_view({'post': 'utiliser'}), 
         name='code-promo-utiliser'),
]