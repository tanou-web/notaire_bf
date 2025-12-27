# apps/core/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import CoreConfiguration, CorePage
from .serializers import (
    CoreConfigurationSerializer,
    CorePageSerializer,
    CorePageCreateSerializer
)


class CoreConfigurationViewSet(viewsets.ModelViewSet):
    """API pour la configuration système (admin seulement)"""
    queryset = CoreConfiguration.objects.all()
    serializer_class = CoreConfigurationSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['cle', 'description']


class CorePageViewSet(viewsets.ModelViewSet):
    """API pour les pages CMS"""
    queryset = CorePage.objects.all()
    serializer_class = CorePageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['publie']
    search_fields = ['titre', 'slug', 'contenu']
    ordering_fields = ['ordre', 'titre', 'date_publication', 'created_at']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CorePageCreateSerializer
        return CorePageSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrer par défaut les pages publiées pour le public
        if not self.request.user.is_staff:
            queryset = queryset.filter(publie=True)
        return queryset
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    @action(detail=True, methods=['get'], url_path='par-slug')
    def par_slug(self, request, slug=None):
        """Récupérer une page par son slug"""
        try:
            page = self.get_queryset().get(slug=slug, publie=True)
            serializer = self.get_serializer(page)
            return Response(serializer.data)
        except CorePage.DoesNotExist:
            return Response(
                {'error': 'Page non trouvée'},
                status=404
            )

