# apps/stats/urls.py - VERSION SIMPLE ET FONCTIONNELLE
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import HttpResponse
from . import views

# Création du router
router = DefaultRouter()

# Enregistrement des ViewSets (ils existent tous dans votre views.py)
router.register(r'visites', views.StatsVisiteViewSet, basename='stats-visite')
router.register(r'pages', views.PageVueViewSet, basename='page-vue')
router.register(r'referents', views.ReferentViewSet, basename='referent')
router.register(r'pays', views.PaysVisiteViewSet, basename='pays-visite')
router.register(r'periodes', views.PeriodeActiveViewSet, basename='periode-active')

# URL patterns
urlpatterns = [
    # Routes du router (CRUD automatique)
    path('', include(router.urls)),
    
    # Endpoints personnalisés
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('tendances/', views.TendancesView.as_view(), name='tendances'),
    path('rapport/', views.GenererRapportView.as_view(), name='generer-rapport'),
    path('export/', views.ExportStatsView.as_view(), name='export-stats'),
    path('synchro/', views.SynchroniserStatsView.as_view(), name='synchro-stats'),
    path('alertes/', views.AlertesView.as_view(), name='alertes'),
]