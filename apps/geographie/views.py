from argparse import Action
from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from apps.communications import models
from .models import GeographieRegion, GeographieVille
from .serializers import RegionSerializer, VilleSerializer
from rest_framework.decorators import action

class RegionViewSet(viewsets.ModelViewSet):
    queryset = GeographieRegion.objects.all().order_by('ordre', 'nom')
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['code','nom', 'ordre']
    search_fields = ['nom', 'description', 'code']
    ordering_fields = ['nom', 'ordre', 'created_at']
    ordering = ['ordre']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def villes(self, request, pk=None):
        region = self.get_object()
        villes = GeographieVille.objects.filter(region=region)
        serializer = VilleSerializer(villes, many=True)
        return Response(serializer.data) 
         
class VilleViewSet(viewsets.ModelViewSet):
    queryset = GeographieVille.objects.all().order_by('nom')
    serializer_class = VilleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region','region_code']
    search_fields = ['nom', 'code_postal']
    ordering = ['nom', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()