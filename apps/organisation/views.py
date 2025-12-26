# apps/organisation/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg
from datetime import date, timedelta

from .models import OrganisationMembrebureau
from .serializers import (
    MembreBureauSerializer, MembreBureauMinimalSerializer,
    MembreBureauCreateSerializer, MembreBureauUpdateSerializer,
    BureauStatsSerializer
)

class MembreBureauViewSet(viewsets.ModelViewSet):
    """
    API pour les membres du bureau
    - GET /api/membres-bureau/ : Liste publique des membres
    - GET /api/membres-bureau/{id}/ : Détail d'un membre
    - POST /api/membres-bureau/ : Création (admin seulement)
    - PUT/PATCH /api/membres-bureau/{id}/ : Mise à jour (admin seulement)
    - DELETE /api/membres-bureau/{id}/ : Suppression (admin seulement)
    """
    
    queryset = OrganisationMembrebureau.objects.all()
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['poste', 'actif']
    search_fields = ['nom', 'prenom', 'poste', 'email']
    ordering_fields = ['ordre', 'nom', 'prenom', 'date_entree']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MembreBureauMinimalSerializer
        elif self.action == 'create':
            return MembreBureauCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MembreBureauUpdateSerializer
        return MembreBureauSerializer
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        """Optimiser les requêtes selon l'action"""
        queryset = super().get_queryset()
        
        # Filtrer par défaut les membres actifs pour le public
        if not self.request.user.is_staff:
            queryset = queryset.filter(actif=True)
        
        # Order par défaut
        if not self.request.query_params.get('ordering'):
            queryset = queryset.order_by('ordre', 'nom', 'prenom')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def en_mandat(self, request):
        """Récupérer uniquement les membres actuellement en mandat"""
        queryset = self.get_queryset().filter(actif=True)
        
        # Filtrer par mandat actuel
        today = date.today()
        queryset = queryset.filter(
            Q(mandat_debut__lte=today) & Q(mandat_fin__gte=today) |
            Q(mandat_debut__isnull=True) & Q(mandat_fin__isnull=True)
        ).order_by('ordre')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_poste(self, request):
        """Grouper les membres par poste"""
        queryset = self.get_queryset().filter(actif=True)
        
        # Grouper par poste
        postes = {}
        for poste_display, poste_value in OrganisationMembrebureau.POSTE_CHOICES:
            membres = queryset.filter(poste=poste_value).order_by('ordre')
            if membres.exists():
                postes[poste_display] = MembreBureauMinimalSerializer(
                    membres, many=True, context={'request': request}
                ).data
        
        return Response(postes)
    
    @action(detail=False, methods=['get'])
    def bureau_executif(self, request):
        """Récupérer uniquement le bureau exécutif (postes principaux)"""
        postes_executifs = [
            'president', 'vice_president', 
            'secretaire', 'secretaire_adjoint',
            'tresorier', 'tresorier_adjoint'
        ]
        
        queryset = self.get_queryset().filter(
            actif=True,
            poste__in=postes_executifs
        ).order_by('ordre')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Activer un membre du bureau"""
        membre = self.get_object()
        membre.actif = True
        membre.save()
        
        return Response({
            'status': 'success',
            'message': f'Membre {membre.nom_complet} activé',
            'membre': MembreBureauSerializer(membre).data
        })
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactiver un membre du bureau"""
        membre = self.get_object()
        membre.actif = False
        membre.save()
        
        return Response({
            'status': 'success',
            'message': f'Membre {membre.nom_complet} désactivé',
            'membre': MembreBureauSerializer(membre).data
        })

class BureauStatsAPIView(APIView):
    """API pour les statistiques du bureau"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Vérifier les permissions (admin seulement)
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission non accordée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Statistiques globales
        total_membres = OrganisationMembrebureau.objects.count()
        membres_actifs = OrganisationMembrebureau.objects.filter(actif=True).count()
        
        # Membres en mandat actuellement
        today = date.today()
        membres_en_mandat = OrganisationMembrebureau.objects.filter(
            actif=True,
            mandat_debut__lte=today,
            mandat_fin__gte=today
        ).count()
        
        # Répartition par poste
        repartition_par_poste = {}
        for poste_display, poste_value in OrganisationMembrebureau.POSTE_CHOICES:
            count = OrganisationMembrebureau.objects.filter(
                poste=poste_value, actif=True
            ).count()
            if count > 0:
                repartition_par_poste[poste_display] = count
        
        # Ancienneté moyenne
        membres_avec_date = OrganisationMembrebureau.objects.filter(
            date_entree__isnull=False
        )
        if membres_avec_date.exists():
            # Calcul de l'ancienneté en années
            total_anciennete = 0
            for membre in membres_avec_date:
                anciennete = (date.today() - membre.date_entree).days / 365.25
                total_anciennete += anciennete
            
            anciennete_moyenne = total_anciennete / membres_avec_date.count()
        else:
            anciennete_moyenne = 0
        
        data = {
            'total_membres': total_membres,
            'membres_actifs': membres_actifs,
            'membres_en_mandat': membres_en_mandat,
            'repartition_par_poste': repartition_par_poste,
            'anciennete_moyenne': round(anciennete_moyenne, 1)
        }
        
        serializer = BureauStatsSerializer(data)
        return Response(serializer.data)

class BureauPublicAPIView(APIView):
    """API publique pour le bureau exécutif"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Récupérer les membres du bureau exécutif actifs
        postes_executifs = [
            'president', 'vice_president', 
            'secretaire', 'secretaire_adjoint',
            'tresorier', 'tresorier_adjoint'
        ]
        
        membres = OrganisationMembrebureau.objects.filter(
            actif=True,
            poste__in=postes_executifs
        ).order_by('ordre')
        
        # Organiser par poste
        bureau_organise = {}
        for poste_display, poste_value in OrganisationMembrebureau.POSTE_CHOICES:
            if poste_value in postes_executifs:
                membres_poste = membres.filter(poste=poste_value)
                if membres_poste.exists():
                    bureau_organise[poste_display] = MembreBureauMinimalSerializer(
                        membres_poste, many=True, context={'request': request}
                    ).data
        
        # Ajouter les conseillers séparément
        conseillers = OrganisationMembrebureau.objects.filter(
            actif=True, poste='conseiller'
        ).order_by('ordre')
        
        if conseillers.exists():
            bureau_organise['conseillers'] = MembreBureauMinimalSerializer(
                conseillers, many=True, context={'request': request}
            ).data
        
        return Response(bureau_organise)