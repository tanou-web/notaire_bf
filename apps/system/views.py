# apps/system/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from apps.system.serializers import SystemStatsSerializer
from .models import (
    SystemConfig, SystemLog, MaintenanceWindow, SystemMetric,
    APIKey, ScheduledTask, SystemHealth, SystemNotification,
    SystemEmailprofessionnel
)
from .serializers import (
    SystemConfigSerializer, SystemLogSerializer,
    MaintenanceWindowSerializer, SystemMetricSerializer,
    APIKeySerializer, ScheduledTaskSerializer,
    SystemHealthSerializer, SystemNotificationSerializer,
    SystemStatsSerializer, SystemAlertSerializer,
    SystemEmailprofessionnelSerializer
)


class SystemEmailprofessionnelViewSet(viewsets.ModelViewSet):
    """API pour la gestion des emails professionnels (10 emails selon livrables)"""
    queryset = SystemEmailprofessionnel.objects.all()
    serializer_class = SystemEmailprofessionnelSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['actif', 'utilisateur']
    search_fields = ['email', 'description']
    ordering_fields = ['email', 'created_at']
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Liste des emails actifs"""
        emails_actifs = self.get_queryset().filter(actif=True)
        serializer = self.get_serializer(emails_actifs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Liste des emails disponibles (non assignés)"""
        emails_disponibles = self.get_queryset().filter(actif=True, utilisateur__isnull=True)
        serializer = self.get_serializer(emails_disponibles, many=True)
        return Response(serializer.data)


# Les autres vues peuvent être ajoutées ici si nécessaire
# Pour l'instant, on se concentre sur SystemEmailprofessionnel

