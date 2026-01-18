# apps/notaires/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404

from .models import NotairesNotaire, NotairesCotisation, NotairesStagiaire
from .serializers import (
    NotaireSerializer, NotaireMinimalSerializer,
    NotaireCreateSerializer, NotaireUpdateSerializer,
    NotaireStatsSerializer, CotisationSerializer,
    StagiaireSerializer
)

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
    ordering_fields = ['nom', 'prenom', 'total_ventes', 'total_cotisations', 'created_at']
    parser_classes = [MultiPartParser, FormParser]  # Pour l'upload de photos
    
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
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def demandes(self, request, pk=None):
        """Récupérer les demandes assignées à un notaire"""
        notaire = self.get_object()
        
        try:
            from apps.ventes.models import Demande
            from apps.ventes.serializers import DemandeSerializer
            
            demandes = Demande.objects.filter(notaire=notaire).select_related(
                'document'
            ).order_by('-created_at')
            
            page = self.paginate_queryset(demandes)
            if page is not None:
                serializer = DemandeSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = DemandeSerializer(demandes, many=True)
            return Response(serializer.data)
            
        except ImportError:
            return Response({
                'detail': 'Module demandes non disponible'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def statistiques(self, request, pk=None):
        """Récupérer les statistiques détaillées d'un notaire"""
        notaire = self.get_object()
        
        try:
            from apps.ventes.models import Demande
            
            # Statistiques par statut
            stats = Demande.objects.filter(notaire=notaire).aggregate(
                total=Count('id'),
                en_attente_paiement=Count('id', filter=Q(statut='attente_paiement')),
                en_traitement=Count('id', filter=Q(statut='en_traitement')),
                terminees=Count('id', filter=Q(statut='termine')),
                annulees=Count('id', filter=Q(statut='annule')),
                montant_total=Sum('montant_total')
            )
            
            # Dernières demandes
            dernieres_demandes = Demande.objects.filter(
                notaire=notaire
            ).order_by('-created_at')[:5]
            
            # Statistiques mensuelles
            mois_dernier = timezone.now() - timedelta(days=30)
            stats_mensuelles = Demande.objects.filter(
                notaire=notaire,
                created_at__gte=mois_dernier
            ).aggregate(
                mensuel=Count('id'),
                mensuel_montant=Sum('montant_total')
            )
            
            total = stats['total'] or 0
            terminees = stats['terminees'] or 0
            
            data = {
                'notaire': {
                    'id': notaire.id,
                    'nom_complet': f"{notaire.nom} {notaire.prenom}",
                    'matricule': notaire.matricule,
                    'email': notaire.email,
                    'telephone': notaire.telephone,
                    'region': notaire.region.nom if notaire.region else None,
                    'ville': notaire.ville.nom if notaire.ville else None,
                    'total_ventes': float(notaire.total_ventes),
                    'total_cotisations': float(notaire.total_cotisations),
                },
                'statistiques': {
                    'globales': {
                        'total_demandes': total,
                        'demandes_en_attente_paiement': stats['en_attente_paiement'] or 0,
                        'demandes_en_traitement': stats['en_traitement'] or 0,
                        'demandes_terminees': terminees,
                        'demandes_annulees': stats['annulees'] or 0,
                        'montant_total': float(stats['montant_total'] or 0),
                    },
                    'mensuelles': {
                        'demandes': stats_mensuelles['mensuel'] or 0,
                        'montant': float(stats_mensuelles['mensuel_montant'] or 0),
                    },
                    'performance': {
                        'taux_completion': round(
                            terminees / max(total, 1) * 100, 1
                        ) if total > 0 else 0,
                    }
                },
                'dernieres_demandes': [
                    {
                        'id': d.id,
                        'reference': d.reference,
                        'client_nom': d.nom_complet_client,
                        'montant': float(d.montant_total),
                        'statut': d.get_statut_display() if hasattr(d, 'get_statut_display') else d.statut,
                        'created_at': d.created_at,
                    }
                    for d in dernieres_demandes
                ]
            }
            
            return Response(data)
            
        except ImportError:
            # Retourner des statistiques basiques si l'app ventes n'est pas disponible
            return Response({
                'notaire': {
                    'id': notaire.id,
                    'nom_complet': f"{notaire.nom} {notaire.prenom}",
                    'matricule': notaire.matricule,
                },
                'message': 'Statistiques détaillées non disponibles',
                'statistiques_basiques': {
                    'total_ventes': float(notaire.total_ventes),
                    'total_cotisations': float(notaire.total_cotisations),
                }
            })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def cotisations(self, request, pk=None):
        """Récupérer les cotisations d'un notaire"""
        notaire = self.get_object()
        cotisations = notaire.cotisations.all().order_by('-annee')
        
        serializer = CotisationSerializer(cotisations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Activer un notaire"""
        notaire = self.get_object()
        notaire.actif = True
        notaire.save()
        
        return Response({
            'status': 'success',
            'message': f'Notaire {notaire.nom} {notaire.prenom} activé',
            'notaire': NotaireMinimalSerializer(notaire).data
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
            'notaire': NotaireMinimalSerializer(notaire).data
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
        
        # Derniers inscrits
        derniers_notaires = NotairesNotaire.objects.order_by(
            '-created_at'
        )[:5].values(
            'id', 'nom', 'prenom', 'created_at'
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


class CotisationViewSet(viewsets.ModelViewSet):
    """API pour les cotisations des notaires"""
    queryset = NotairesCotisation.objects.all()
    serializer_class = CotisationSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notaire', 'annee', 'statut']


class RechercheNotairesAPIView(APIView):
    """API de recherche avancée de notaires"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Récupérer les paramètres
        region_id = request.query_params.get('region')
        ville_id = request.query_params.get('ville')
        search = request.query_params.get('search', '')
        actif = request.query_params.get('actif', 'true').lower() == 'true'
        
        queryset = NotairesNotaire.objects.all()
        
        # Filtres
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        if ville_id:
            queryset = queryset.filter(ville_id=ville_id)
        
        if actif:
            queryset = queryset.filter(actif=True)
        
        # Recherche texte
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(matricule__icontains=search) |
                Q(email__icontains=search) |
                Q(region__nom__icontains=search) |
                Q(ville__nom__icontains=search)
            ).select_related('region', 'ville')
        
        serializer = NotaireMinimalSerializer(queryset, many=True)
        
        # Récupérer les régions et villes disponibles pour les filtres
        regions = NotairesNotaire.objects.exclude(region__isnull=True).values(
            'region__id', 'region__nom'
        ).distinct().order_by('region__nom')
        
        villes = NotairesNotaire.objects.exclude(ville__isnull=True).values(
            'ville__id', 'ville__nom'
        ).distinct().order_by('ville__nom')
        
        return Response({
            'count': queryset.count(),
            'results': serializer.data,
            'filtres_disponibles': {
                'regions': list(regions),
                'villes': list(villes),
            }
        })

class StagiaireViewSet(viewsets.ModelViewSet):
    """API pour la gestion des stagiaires notaires"""
    queryset = NotairesStagiaire.objects.all()
    serializer_class = StagiaireSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['notaire_maitre', 'statut']
    search_fields = ['nom', 'prenom', 'email']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()