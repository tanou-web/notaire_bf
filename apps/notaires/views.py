# apps/notaires/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import NotairesNotaire, Region, Ville
from .serializers import (
    NotaireSerializer, NotaireMinimalSerializer,
    NotaireCreateSerializer, NotaireUpdateSerializer,
    RegionSerializer, VilleSerializer, NotaireStatsSerializer
)

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les régions"""
    queryset = Region.objects.all().order_by('nom')
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'code']

class VilleViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les villes"""
    queryset = Ville.objects.all().order_by('nom')
    serializer_class = VilleSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['nom', 'code_postal']
    filterset_fields = ['region']

class NotaireViewSet(viewsets.ModelViewSet):
    """
    API complète pour les notaires
    - Liste publique : GET /api/notaires/
    - Détail public : GET /api/notaires/{id}/
    - Création : POST /api/notaires/ (admin seulement)
    - Modification : PUT/PATCH /api/notaires/{id}/ (admin seulement)
    """
    
    queryset = NotairesNotaire.objects.all().order_by('nom', 'prenom')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region', 'ville', 'actif']
    search_fields = ['nom', 'prenom', 'matricule', 'email']
    ordering_fields = ['nom', 'prenom', 'total_ventes', 'total_cotisations', 'date_inscription']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotaireMinimalSerializer
        elif self.action == 'create':
            return NotaireCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NotaireUpdateSerializer
        return NotaireSerializer
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        """Optimiser les requêtes selon l'action"""
        queryset = super().get_queryset()
        
        # Pour la liste, on précharge les relations nécessaires
        if self.action == 'list':
            queryset = queryset.select_related('region', 'ville')
        
        # Filtrer les notaires inactifs si pas admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(actif=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def demandes(self, request, pk=None):
        """Récupérer les demandes assignées à un notaire"""
        notaire = self.get_object()
        from apps.demandes.serializers import DemandeSerializer
        
        demandes = notaire.demandesdemande_set.all().select_related(
            'document', 'utilisateur'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(demandes)
        if page is not None:
            serializer = DemandeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DemandeSerializer(demandes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Récupérer les statistiques détaillées d'un notaire"""
        notaire = self.get_object()
        from apps.demandes.models import DemandesDemande
        
        # Statistiques par statut
        stats = DemandesDemande.objects.filter(notaire=notaire).aggregate(
            total=Count('id'),
            en_attente=Count('id', filter=Q(statut='en_attente_traitement')),
            en_traitement=Count('id', filter=Q(statut='en_traitement')),
            terminees=Count('id', filter=Q(statut='document_envoye_email')),
            annulees=Count('id', filter=Q(statut='annule')),
            montant_total=Sum('montant_total'),
            commission_total=Sum('frais_commission')
        )
        
        # Dernières demandes
        dernieres_demandes = DemandesDemande.objects.filter(
            notaire=notaire
        ).order_by('-created_at')[:5]
        
        # Statistiques mensuelles
        mois_dernier = timezone.now() - timedelta(days=30)
        stats_mensuelles = DemandesDemande.objects.filter(
            notaire=notaire,
            created_at__gte=mois_dernier
        ).aggregate(
            mensuel=Count('id'),
            mensuel_montant=Sum('montant_total')
        )
        
        data = {
            'notaire': NotaireSerializer(notaire).data,
            'statistiques': {
                'globales': {
                    'total_demandes': stats['total'] or 0,
                    'demandes_en_attente': stats['en_attente'] or 0,
                    'demandes_en_traitement': stats['en_traitement'] or 0,
                    'demandes_terminees': stats['terminees'] or 0,
                    'demandes_annulees': stats['annulees'] or 0,
                    'montant_total': float(stats['montant_total'] or 0),
                    'commission_total': float(stats['commission_total'] or 0),
                },
                'mensuelles': {
                    'demandes': stats_mensuelles['mensuel'] or 0,
                    'montant': float(stats_mensuelles['mensuel_montant'] or 0),
                },
                'performance': {
                    'taux_completion': round(
                        (stats['terminees'] or 0) / max(stats['total'] or 1, 1) * 100, 1
                    ),
                    'temps_moyen_traitement': 48,  # À calculer réellement
                }
            },
            'dernieres_demandes': [
                {
                    'id': d.id,
                    'reference': d.reference,
                    'document': d.document.nom if d.document else '',
                    'statut': d.get_statut_display(),
                    'created_at': d.created_at,
                }
                for d in dernieres_demandes
            ]
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Activer un notaire"""
        notaire = self.get_object()
        notaire.actif = True
        notaire.save()
        
        return Response({
            'status': 'success',
            'message': f'Notaire {notaire.nom} {notaire.prenom} activé',
            'notaire': NotaireSerializer(notaire).data
        })
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactiver un notaire"""
        notaire = self.get_object()
        notaire.actif = False
        notaire.save()
        
        return Response({
            'status': 'success',
            'message': f'Notaire {notaire.nom} {notaire.prenom} désactivé',
            'notaire': NotaireSerializer(notaire).data
        })

class NotaireStatsAPIView(APIView):
    """API pour les statistiques globales des notaires"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Vérifier les permissions (admin seulement)
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission non accordée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.demandes.models import DemandesDemande
        
        # Statistiques globales
        stats_globales = NotairesNotaire.objects.aggregate(
            total=Count('id'),
            actifs=Count('id', filter=Q(actif=True)),
            inactifs=Count('id', filter=Q(actif=False)),
            total_ventes=Sum('total_ventes'),
            total_cotisations=Sum('total_cotisations')
        )
        
        # Distribution par région
        distribution_region = NotairesNotaire.objects.values(
            'region__nom'
        ).annotate(
            count=Count('id'),
            ventes=Sum('total_ventes')
        ).order_by('-count')
        
        # Top 10 notaires par ventes
        top_ventes = NotairesNotaire.objects.filter(
            total_ventes__gt=0
        ).order_by('-total_ventes')[:10].values(
            'id', 'nom', 'prenom', 'region__nom', 'total_ventes'
        )
        
        # Dernières activités
        derniers_notaires = NotairesNotaire.objects.order_by(
            '-date_inscription'
        )[:5].values(
            'id', 'nom', 'prenom', 'date_inscription'
        )
        
        data = {
            'globales': {
                'total_notaires': stats_globales['total'] or 0,
                'notaires_actifs': stats_globales['actifs'] or 0,
                'notaires_inactifs': stats_globales['inactifs'] or 0,
                'chiffre_affaires_total': float(stats_globales['total_ventes'] or 0),
                'cotisations_total': float(stats_globales['total_cotisations'] or 0),
            },
            'distribution_par_region': list(distribution_region),
            'top_ventes': list(top_ventes),
            'derniers_inscrits': list(derniers_notaires),
        }
        
        return Response(data)