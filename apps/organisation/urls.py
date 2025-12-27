# apps/organisation/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MembreBureauViewSet, BureauStatsAPIView, BureauPublicAPIView,
    HistoriqueViewSet, MissionViewSet
)

router = DefaultRouter()
router.register(r'membres-bureau', MembreBureauViewSet, basename='membre-bureau')
router.register(r'historique', HistoriqueViewSet, basename='historique')
router.register(r'missions', MissionViewSet, basename='mission')

urlpatterns = [
    # API REST standard
    path('api/', include(router.urls)),
    
    # Statistiques (admin)
    path('api/organisation/stats/', 
         BureauStatsAPIView.as_view(), 
         name='bureau-stats'),
    
    # Vue publique organisée
    path('api/organisation/bureau/', 
         BureauPublicAPIView.as_view(), 
         name='bureau-public'),
    
    # Endpoints spécifiques
    path('api/membres-bureau/en-mandat/', 
         MembreBureauViewSet.as_view({'get': 'en_mandat'}), 
         name='membres-en-mandat'),
    
    path('api/membres-bureau/par-poste/', 
         MembreBureauViewSet.as_view({'get': 'par_poste'}), 
         name='membres-par-poste'),
    
    path('api/membres-bureau/bureau-executif/', 
         MembreBureauViewSet.as_view({'get': 'bureau_executif'}), 
         name='bureau-executif'),
    
    path('api/membres-bureau/<int:pk>/activer/', 
         MembreBureauViewSet.as_view({'post': 'activer'}), 
         name='membre-activer'),
    
    path('api/membres-bureau/<int:pk>/desactiver/', 
         MembreBureauViewSet.as_view({'post': 'desactiver'}), 
         name='membre-desactiver'),
]