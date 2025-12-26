from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'configs', views.SystemConfigViewSet, basename='system-config')
router.register(r'logs', views.SystemLogViewSet, basename='system-log')
router.register(r'maintenance', views.MaintenanceWindowViewSet, basename='maintenance')
router.register(r'metrics', views.SystemMetricViewSet, basename='metric')
router.register(r'api-keys', views.APIKeyViewSet, basename='api-key')
router.register(r'tasks', views.ScheduledTaskViewSet, basename='scheduled-task')
router.register(r'health', views.SystemHealthViewSet, basename='system-health')
router.register(r'notifications', views.SystemNotificationViewSet, basename='notification')

# URLs personnalisées
urlpatterns = [
    # API
    path('api/', include(router.urls)),
    
    # Tableau de bord
    path('api/dashboard/', views.SystemDashboardView.as_view(), name='system-dashboard'),
    
    # Alertes
    path('api/alerts/', views.SystemAlertView.as_view(), name='system-alerts'),
    
    # Informations système
    path('api/info/', views.system_info, name='system-info'),
    
    # Actions système
    path('api/restart/', views.system_restart, name='system-restart'),
    
    # Interface web (si nécessaire)
    path('dashboard/', views.SystemDashboardView.as_view(), name='system-web-dashboard'),
]