from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action, permission_classes

from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

from django_filters import rest_framework as django_filters
from django.utils import timezone
from .models import ActualitesActualite
from .serializers import ActualiteSerializer, ActualiteListSerializer
from django.db.models import Count, Q, Sum, Avg, F


class ActualiteFilter(django_filters.FilterSet):
    """Filtres personnalisés pour les actualités"""
    date_debut = django_filters.DateFilter(field_name="date_publication", lookup_expr='gte')
    date_fin = django_filters.DateFilter(field_name="date_publication", lookup_expr='lte')
    categorie = django_filters.ChoiceFilter(choices=ActualitesActualite.CATEGORIE_CHOICES)
    
    class Meta:
        model = ActualitesActualite
        fields = ['categorie', 'important', 'featured', 'date_debut', 'date_fin']


class ActualiteViewSet(viewsets.ModelViewSet):
    queryset = ActualitesActualite.objects.all().order_by('-date_publication', '-created_at')
    serializer_class = ActualiteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ActualiteFilter
    search_fields = ['titre', 'contenu', 'resume', 'slug']
    ordering_fields = ['date_publication', 'created_at', 'vue', 'titre']
    ordering = ['-date_publication']
    parser_classes = [MultiPartParser, FormParser]  # Pour upload d'images

    def get_serializer_class(self):
        """Utiliser un serializer différent pour la liste"""
        if self.action == 'list':
            return ActualiteListSerializer
        return ActualiteSerializer

    def get_queryset(self):
        """Adapter le queryset selon les permissions"""
        queryset = super().get_queryset()

        # Support du paramètre 'q' pour la recherche générale
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(titre__icontains=search_query) |
                Q(contenu__icontains=search_query) |
                Q(resume__icontains=search_query) |
                Q(slug__icontains=search_query)
            )

        # Pour les utilisateurs non authentifiés ou non staff, ne montrer que les actualités publiées
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            queryset = queryset.filter(
                publie=True,
                date_publication__lte=timezone.now()
            )

        return queryset

    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    def get_serializer_context(self):
        """Ajouter le contexte pour les URLs absolues"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def publiees(self, request):
        """Liste des actualités publiées (accessible publiquement)"""
        actualites = self.get_queryset().filter(
            publie=True,
            date_publication__lte=timezone.now()
        ).order_by('-date_publication')
        
        page = self.paginate_queryset(actualites)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(actualites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def importantes(self, request):
        """Actualités importantes et publiées"""
        actualites = self.get_queryset().filter(
            important=True,
            publie=True,
            date_publication__lte=timezone.now()
        ).order_by('-date_publication')
        
        page = self.paginate_queryset(actualites)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(actualites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Actualités mises en avant (featured)"""
        actualites = self.get_queryset().filter(
            featured=True,
            publie=True,
            date_publication__lte=timezone.now()
        ).order_by('-date_publication')
        
        page = self.paginate_queryset(actualites)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(actualites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        queryset = self.get_queryset().filter(
            publie = True,
            date_publication__lte = timezone.now()
        )
        data = {}
        for cat, label in ActualitesActualite.CATEGORIE_CHOICES:
            items = queryset.filter(categorie=cat)
            serializer = self.get_serializer(items, many=True)
            data[label] = serializer.data
        return Response(data)



    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Dernières actualités (limitées)"""
        limite = request.query_params.get('limite', 5)
        try:
            limite = int(limite)
        except ValueError:
            limite = 5
        
        actualites = self.get_queryset().filter(
            publie=True,
            date_publication__lte=timezone.now()
        ).order_by('-date_publication')[:limite]
        
        serializer = self.get_serializer(actualites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def stats(self, request):
        """Statistiques sur les actualités"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'publiees': queryset.filter(publie=True).count(),
            'non_publiees': queryset.filter(publie=False).count(),
            'importantes': queryset.filter(important=True).count(),
            'featured': queryset.filter(featured=True).count(),
            'par_categorie': dict(queryset.values('categorie').annotate(
                count=Count('id')
            ).values_list('categorie', 'count')),
            'vues_total': queryset.aggregate(total=Sum('vue'))['total'] or 0,
            'moyenne_vues': queryset.filter(publie=True).aggregate(
                avg=Avg('vue')
            )['avg'] or 0
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def incrementer_vues(self, request, pk=None):
        """Incrémenter le compteur de vues"""
        ActualitesActualite.objects.filter(pk=pk).update(vue=F('vue') +1)
        actualite = ActualitesActualite.objects.only('vue').get(pk=pk)
        return Response({'vues': actualite.vue})
        
    @action(detail=False, methods=['get'])
    def recherche_avancee(self, request):
        """Recherche avancée dans les actualités"""
        query = request.query_params.get('q', '')
        categorie = request.query_params.get('categorie', '')
        date_debut = request.query_params.get('date_debut', '')
        date_fin = request.query_params.get('date_fin', '')
        
        if not any([query, categorie, date_debut, date_fin]):
            return Response(
                {"detail": "Au moins un paramètre de recherche est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(publie=True, date_publication__lte=timezone.now())
        
        if query:
            queryset = queryset.filter(
                Q(titre__icontains=query) |
                Q(contenu__icontains=query) |
                Q(resume__icontains=query)
            )
        
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        
        if date_debut:
            queryset = queryset.filter(date_publication__gte=date_debut)
        
        if date_fin:
            queryset = queryset.filter(date_publication__lte=date_fin)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def publier(self, request, pk=None):
        """Publier une actualité"""
        actualite = self.get_object()
        if actualite.publie:
            return Response(
                {"detail": "Cette actualité est déjà publiée"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        actualite.publie = True
        if not actualite.date_publication:
            actualite.date_publication = timezone.now()
        actualite.save()
        
        serializer = self.get_serializer(actualite)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def depublier(self, request, pk=None):
        """Dépublier une actualité"""
        actualite = self.get_object()
        if not actualite.publie:
            return Response(
                {"detail": "Cette actualité n'est pas publiée"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        actualite.publie = False
        actualite.save()
        
        serializer = self.get_serializer(actualite)
        return Response(serializer.data)