from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.views.generic import TemplateView
from . import views, api_views, services

# Initialisation du router DRF
router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'visites', api_views.StatsVisiteViewSet, basename='stats-visite')
router.register(r'pages', api_views.PageVueViewSet, basename='page-vue')
router.register(r'referents', api_views.ReferentViewSet, basename='referent')
router.register(r'pays', api_views.PaysVisiteViewSet, basename='pays-visite')
router.register(r'periodes', api_views.PeriodeActiveViewSet, basename='periode-active')
router.register(r'appareils', api_views.AppareilViewSet, basename='appareil')
router.register(r'navigateurs', api_views.NavigateurViewSet, basename='navigateur')

# Création d'un nested router pour les statistiques par visites
visite_router = routers.NestedDefaultRouter(router, r'visites', lookup='visite')
visite_router.register(r'pages', api_views.PageParVisiteViewSet, basename='visite-pages')
visite_router.register(r'referents', api_views.ReferentParVisiteViewSet, basename='visite-referents')

# URL patterns pour l'API
api_urlpatterns = [
    path('', include(router.urls)),
    path('', include(visite_router.urls)),
    
    # Endpoints spéciaux
    path('dashboard/', api_views.DashboardView.as_view(), name='dashboard'),
    path('tendances/', api_views.TendancesView.as_view(), name='tendances'),
    path('rapport/', api_views.GenererRapportView.as_view(), name='generer-rapport'),
    path('export/', api_views.ExportStatsView.as_view(), name='export-stats'),
    path('synchro/', api_views.SynchroniserStatsView.as_view(), name='synchro-stats'),
    path('alertes/', api_views.AlertesView.as_view(), name='alertes'),
]

# URL patterns pour les vues HTML (si besoin d'interface web)
html_urlpatterns = [
    path('', views.StatsDashboardView.as_view(), name='stats-dashboard'),
    path('detail/<str:date>/', views.StatsDetailView.as_view(), name='stats-detail'),
    path('periode/', views.StatsPeriodeView.as_view(), name='stats-periode'),
    path('comparaison/', views.ComparaisonView.as_view(), name='stats-comparaison'),
    path('rapports/', views.RapportsView.as_view(), name='stats-rapports'),
    path('export/html/', views.ExportHTMLView.as_view(), name='stats-export-html'),
    
    # Graphiques et visualisations
    path('graphique/visites/', views.GraphiqueVisitesView.as_view(), name='graphique-visites'),
    path('graphique/pages/', views.GraphiquePagesView.as_view(), name='graphique-pages'),
    path('graphique/sources/', views.GraphiqueSourcesView.as_view(), name='graphique-sources'),
    path('graphique/geographie/', views.GraphiqueGeographieView.as_view(), name='graphique-geographie'),
    path('graphique/temps-reel/', views.TempsReelView.as_view(), name='graphique-temps-reel'),
]

# URL patterns pour les webhooks et intégrations
webhook_urlpatterns = [
    path('track/', views.TrackVisitView.as_view(), name='track-visit'),
    path('webhook/google-analytics/', views.GoogleAnalyticsWebhook.as_view(), name='webhook-ga'),
    path('webhook/matomo/', views.MatomoWebhook.as_view(), name='webhook-matomo'),
    path('pixel/', views.TrackingPixelView.as_view(), name='tracking-pixel'),
]

# URL patterns principales
urlpatterns = [
    # API REST
    path('api/', include(api_urlpatterns)),
    
    # Interface Web
    path('web/', include(html_urlpatterns)),
    
    # Webhooks
    path('webhooks/', include(webhook_urlpatterns)),
    
    # Documentation
    path('doc/', TemplateView.as_view(template_name='stats/documentation.html'), name='stats-doc'),
    path('swagger/', TemplateView.as_view(template_name='stats/swagger.html'), name='stats-swagger'),
    
    # Redirection
    path('', views.StatsRedirectView.as_view(), name='stats-home'),
]