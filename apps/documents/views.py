from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.db.models import Avg, Count, Q
from .models import DocumentsDocument, DocumentsTextelegal
from .serializers import DocumentSerializer, TexteLegalSerializer


class DocumentFilter(django_filters.FilterSet):
    """Filtres personnalisés pour les documents"""
    prix_min = django_filters.NumberFilter(field_name="prix", lookup_expr='gte')
    prix_max = django_filters.NumberFilter(field_name="prix", lookup_expr='lte')
    delai = django_filters.ChoiceFilter(choices=DocumentsDocument.DELAI_CHOICES)
    
    class Meta:
        model = DocumentsDocument
        fields = ['actif', 'delai', 'prix_min', 'prix_max']


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = DocumentsDocument.objects.all().order_by('nom')
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentFilter
    search_fields = ['reference', 'nom', 'description']
    ordering_fields = ['nom', 'prix', 'delai_heures', 'created_at', 'updated_at']
    ordering = ['nom']

    def get_permissions(self):
        """Seuls les admins peuvent créer/modifier/supprimer des documents"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Par défaut, ne montrer que les documents actifs pour les utilisateurs non authentifiés"""
        queryset = super().get_queryset()
        
        # Si l'utilisateur n'est pas admin, ne montrer que les documents actifs
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            queryset = queryset.filter(actif=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Liste des documents actifs seulement"""
        documents = self.get_queryset().filter(actif=True)
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques sur les documents"""
        queryset = self.get_queryset()
        
        stats = {
            'total_documents': queryset.count(),
            'documents_actifs': queryset.filter(actif=True).count(),
            'prix_moyen': queryset.aggregate(prix_moyen=Avg('prix'))['prix_moyen'] or 0,
            'par_delai': {
                choice[0]: queryset.filter(delai_heures=choice[0]).count()
                for choice in DocumentsDocument.DELAI_CHOICES
            }
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recherche_avancee(self, request):
        """Recherche avancée dans les documents"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({"detail": "Paramètre 'q' requis"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recherche dans plusieurs champs
        documents = self.get_queryset().filter(
            Q(nom__icontains=query) |
            Q(description__icontains=query) |
            Q(reference__icontains=query)
        )
        
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)


class TexteLegalFilter(django_filters.FilterSet):
    """Filtres personnalisés pour les textes légaux"""
    date_debut = django_filters.DateFilter(field_name="date_publication", lookup_expr='gte')
    date_fin = django_filters.DateFilter(field_name="date_publication", lookup_expr='lte')
    type = django_filters.ChoiceFilter(choices=DocumentsTextelegal.TYPE_CHOICES)
    
    class Meta:
        model = DocumentsTextelegal
        fields = ['type', 'date_debut', 'date_fin']


class TexteLegalViewSet(viewsets.ModelViewSet):
    queryset = DocumentsTextelegal.objects.all().order_by('type_texte', 'ordre', 'titre')
    serializer_class = TexteLegalSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TexteLegalFilter
    search_fields = ['titre', 'reference', 'type_texte']
    ordering_fields = ['titre', 'type_texte', 'ordre', 'date_publication', 'created_at']
    ordering = ['type_texte', 'ordre', 'titre']

    def get_permissions(self):
        """Seuls les admins peuvent créer/modifier/supprimer des textes légaux"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    def get_serializer_context(self):
        """Ajouter le contexte pour les URLs absolues"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Liste des types de textes légaux disponibles"""
        types = DocumentsTextelegal.objects.values_list('type_texte', flat=True).distinct()
        types_display = [
            {'value': t, 'display': dict(DocumentsTextelegal.TYPE_CHOICES).get(t, t)}
            for t in types
        ]
        return Response(types_display)
    
    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """Groupement des textes légaux par type"""
        result = {}
        queryset = self.get_queryset()
        
        for choix in DocumentsTextelegal.TYPE_CHOICES:
            type_value, type_display = choix
            textes = queryset.filter(type_texte=type_value)
            
            if textes.exists():
                serializer = self.get_serializer(textes, many=True)
                result[type_display] = serializer.data
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        """Rediriger vers le téléchargement du fichier"""
        texte = self.get_object()
        if not texte.fichier:
            return Response(
                {"detail": "Aucun fichier disponible"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'url': texte.fichier,
            'titre': texte.titre,
            'type': texte.get_type_texte_display()
        })