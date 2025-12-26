# apps/ventes/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import (
    Sum, Count, Avg, Q, F, Value, DecimalField,
    Case, When, IntegerField, OuterRef, Subquery, Exists
)
from django.db.models.functions import (
    TruncDate, TruncMonth, TruncYear, Coalesce, Concat
)
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import logging

from .models import (
    VentesSticker, Client, Demande, LigneDemande,
    VentesFacture, Paiement, Panier, ItemPanier,
    AvisClient, CodePromo
)
from .serializers import (
    VentesStickerSerializer, VentesStickerMinimalSerializer, VentesStickerCreateSerializer,
    ClientSerializer, ClientMinimalSerializer, ClientCreateSerializer,
    DemandeSerializer, DemandeCreateSerializer, DemandeUpdateSerializer,
    LigneDemandeSerializer, LigneDemandeCreateSerializer,
    VentesFactureSerializer, PaiementSerializer, PaiementCreateSerializer,
    PanierSerializer, ItemPanierSerializer,
    AvisClientSerializer, CodePromoSerializer,
    VentesStatsSerializer, ClientStatsSerializer, StockStatsSerializer,
    DashboardStatsSerializer
)
from .filters import (
    VentesStickerFilter, ClientFilter, DemandeFilter,
    VentesFactureFilter, PaiementFilter, AvisClientFilter
)

# Configuration du logger
logger = logging.getLogger(__name__)

# ========================================
# PAGINATION PERSONNALISÉE
# ========================================

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LargePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

# ========================================
# UTILITAIRES
# ========================================

def parse_date_safe(date_str, default=None):
    """Parse une date en toute sécurité"""
    if isinstance(date_str, (datetime, timezone.datetime)):
        return date_str.date() if hasattr(date_str, 'date') else date_str
    
    try:
        if date_str:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass
    
    return default or timezone.now().date()

# ========================================
# VIEWSETS STICKERS
# ========================================

class VentesStickerViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des stickers.
    
    Permissions:
    - Liste et détail: Public
    - Création/modification/suppression: Admin seulement
    """
    queryset = VentesSticker.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VentesStickerFilter
    search_fields = ['code', 'nom', 'description', 'categorie', 'tags']
    ordering_fields = ['code', 'nom', 'prix_ht', 'prix_ttc', 'quantite', 'created_at']
    ordering = ['code']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VentesStickerMinimalSerializer
        elif self.action == 'create':
            return VentesStickerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VentesStickerCreateSerializer
        return VentesStickerSerializer
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['list', 'retrieve', 'search', 'disponibles']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ: IsAdminUser() avec parenthèses
    
    def get_queryset(self):
        """Optimiser les requêtes selon l'action"""
        queryset = super().get_queryset()
        
        # Pour le public, ne montrer que les stickers actifs
        if not self.request.user.is_staff:
            queryset = queryset.filter(actif=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Liste des stickers disponibles (en stock)"""
        queryset = self.get_queryset().filter(quantite__gt=0)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_rupture(self, request):
        """Liste des stickers en rupture de stock"""
        queryset = self.get_queryset().filter(
            quantite__lte=F('stock_securite'),
            actif=True
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def populaires(self, request):
        """Liste des stickers populaires - OPTIMISÉ"""
        # ✅ OPTIMISATION: Utiliser un ordre déterministe au lieu de aléatoire
        date_limit = timezone.now() - timedelta(days=90)  # 3 derniers mois
        
        # Sous-requête pour le nombre de ventes
        ventes_par_sticker = LigneDemande.objects.filter(
            sticker=OuterRef('pk'),
            demande__date_creation__gte=date_limit
        ).values('sticker').annotate(
            total_ventes=Sum('quantite')
        ).values('total_ventes')
        
        queryset = self.get_queryset().filter(
            actif=True
        ).annotate(
            ventes_recentes=Coalesce(Subquery(ventes_par_sticker), 0)
        ).order_by('-ventes_recentes', '-est_populaire', '-created_at')[:20]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nouveaux(self, request):
        """Liste des nouveaux stickers"""
        date_limit = timezone.now() - timedelta(days=30)
        queryset = self.get_queryset().filter(
            est_nouveau=True,
            actif=True,
            created_at__gte=date_limit
        ).order_by('-created_at')[:20]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """Groupement des stickers par catégorie - OPTIMISÉ"""
        # ✅ OPTIMISATION: Utiliser une seule requête groupée
        from django.db.models import Value as V
        from django.db.models.functions import Concat
        
        queryset = self.get_queryset().filter(actif=True)
        
        # Annoter la catégorie (avec 'Non classé' pour les null)
        queryset = queryset.annotate(
            categorie_affichage=Case(
                When(categorie__isnull=False, then=F('categorie')),
                default=V('Non classé'),
                output_field=models.CharField()
            )
        )
        
        # Grouper par catégorie en une seule requête
        categories_data = queryset.values('categorie_affichage').annotate(
            nombre_stickers=Count('id'),
            stickers_ids=models.ArrayAgg('id', ordering=('created_at',))
        ).order_by('categorie_affichage')
        
        # Récupérer les stickers pour chaque catégorie
        result = {}
        for cat_data in categories_data:
            categorie = cat_data['categorie_affichage']
            stickers_ids = cat_data['stickers_ids'][:10]  # Limiter à 10 par catégorie
            
            stickers = VentesSticker.objects.filter(
                id__in=stickers_ids
            ).order_by('-created_at')
            
            serializer = VentesStickerMinimalSerializer(
                stickers, many=True, context={'request': request}
            )
            result[categorie] = {
                'nombre_stickers': cat_data['nombre_stickers'],
                'stickers': serializer.data
            }
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Statistiques détaillées d'un sticker"""
        sticker = self.get_object()
        
        # Statistiques de vente avec requêtes optimisées
        stats = LigneDemande.objects.filter(sticker=sticker).aggregate(
            total_vendu=Coalesce(Sum('quantite'), 0),
            chiffre_affaires=Coalesce(Sum('montant_ttc'), Decimal('0')),
            moyenne_quantite=Coalesce(Avg('quantite'), Decimal('0')),
            nombre_commandes=Count('demande', distinct=True)
        )
        
        # Dernières ventes (limitées)
        dernieres_ventes = LigneDemande.objects.filter(
            sticker=sticker
        ).select_related('demande', 'demande__client').order_by(
            '-demande__date_creation'
        )[:10]
        
        data = {
            'sticker': VentesStickerSerializer(sticker, context={'request': request}).data,
            'statistiques': {
                'total_vendu': stats['total_vendu'],
                'chiffre_affaires': float(stats['chiffre_affaires']),
                'moyenne_quantite': float(stats['moyenne_quantite']),
                'nombre_commandes': stats['nombre_commandes'],
                'stock_actuel': sticker.quantite,
                'taux_rotation': round(
                    (stats['total_vendu'] / max(sticker.quantite, 1)), 
                    2
                ) if sticker.quantite > 0 else 0
            },
            'dernieres_ventes': [
                {
                    'demande': {
                        'numero': l.demande.numero,
                        'date': l.demande.date_creation,
                        'client': l.demande.client.nom_complet if l.demande.client else None
                    },
                    'quantite': l.quantite,
                    'montant': float(l.montant_ttc)
                }
                for l in dernieres_ventes
            ]
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def ajuster_stock(self, request, pk=None):
        """Ajuster le stock d'un sticker avec historisation"""
        sticker = self.get_object()
        quantite = request.data.get('quantite')
        operation = request.data.get('operation', 'ajouter')  # 'ajouter' ou 'retirer'
        raison = request.data.get('raison', '')
        
        if not quantite:
            raise ValidationError({'quantite': 'La quantité est requise'})
        
        try:
            quantite = int(quantite)
            if quantite <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise ValidationError({'quantite': 'La quantité doit être un entier positif'})
        
        ancien_stock = sticker.quantite
        
        if operation == 'ajouter':
            sticker.quantite += quantite
            message = f"Stock augmenté de {quantite}"
        elif operation == 'retirer':
            if sticker.quantite < quantite:
                raise ValidationError(
                    {'quantite': f'Stock insuffisant. Disponible: {sticker.quantite}'}
                )
            sticker.quantite -= quantite
            message = f"Stock réduit de {quantite}"
        else:
            raise ValidationError(
                {'operation': "Opération invalide. Utiliser 'ajouter' ou 'retirer'"}
            )
        
        # ✅ LOG: Historisation de l'ajustement
        logger.info(
            f"Ajustement stock - Sticker: {sticker.code}, "
            f"Ancien: {ancien_stock}, Nouveau: {sticker.quantite}, "
            f"Opération: {operation}, Quantité: {quantite}, "
            f"Raison: {raison}, Utilisateur: {request.user}"
        )
        
        sticker.save()
        
        return Response({
            'status': 'success',
            'message': message,
            'sticker': {
                'id': sticker.id,
                'code': sticker.code,
                'nom': sticker.nom,
                'ancien_stock': ancien_stock,
                'nouveau_stock': sticker.quantite,
                'variation': sticker.quantite - ancien_stock
            },
            'details': {
                'operation': operation,
                'quantite': quantite,
                'raison': raison,
                'date': timezone.now(),
                'utilisateur': request.user.username if request.user.is_authenticated else None
            }
        })

# ========================================
# VIEWSETS CLIENTS
# ========================================

class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des clients"""
    queryset = Client.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClientFilter
    search_fields = ['code_client', 'nom', 'prenom', 'email', 'telephone', 'entreprise', 'ville']
    ordering_fields = ['nom', 'prenom', 'email', 'montant_total_achats', 'nombre_commandes', 'created_at']
    ordering = ['nom', 'prenom']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClientMinimalSerializer
        elif self.action == 'create':
            return ClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClientCreateSerializer
        return ClientSerializer
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['create']:  # Inscription client
            return [permissions.AllowAny()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que leur propre compte
        if not self.request.user.is_staff:
            # On suppose que le client est lié à l'utilisateur par email
            queryset = queryset.filter(email=self.request.user.email)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def recherche(self, request):
        """Recherche avancée de clients"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filtres additionnels
        montant_min = request.query_params.get('montant_min')
        montant_max = request.query_params.get('montant_max')
        commandes_min = request.query_params.get('commandes_min')
        commandes_max = request.query_params.get('commandes_max')
        
        if montant_min:
            queryset = queryset.filter(montant_total_achats__gte=montant_min)
        if montant_max:
            queryset = queryset.filter(montant_total_achats__lte=montant_max)
        if commandes_min:
            queryset = queryset.filter(nombre_commandes__gte=commandes_min)
        if commandes_max:
            queryset = queryset.filter(nombre_commandes__lte=commandes_max)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def demandes(self, request, pk=None):
        """Liste des demandes d'un client"""
        client = self.get_object()
        
        # Vérifier que l'utilisateur a le droit de voir ces demandes
        if not request.user.is_staff and client.email != request.user.email:
            raise PermissionDenied("Vous n'avez pas accès à ces demandes")
        
        demandes = client.demandes.all().order_by('-date_creation')
        
        page = self.paginate_queryset(demandes)
        if page is not None:
            serializer = DemandeSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = DemandeSerializer(demandes, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Statistiques détaillées d'un client"""
        client = self.get_object()
        
        # Vérifier les permissions
        if not request.user.is_staff and client.email != request.user.email:
            raise PermissionDenied("Vous n'avez pas accès à ces statistiques")
        
        demandes = client.demandes.all()
        stats = demandes.aggregate(
            total_demandes=Count('id'),
            demandes_en_attente=Count('id', filter=Q(statut='en_attente')),
            demandes_confirmees=Count('id', filter=Q(statut='confirmee')),
            demandes_expediees=Count('id', filter=Q(statut='expediee')),
            demandes_livrees=Count('id', filter=Q(statut='livree')),
            montant_total=Coalesce(Sum('montant_total_ttc'), Decimal('0'))
        )
        
        # Période d'activité
        if client.date_premier_achat and client.date_dernier_achat:
            jours_activite = (client.date_dernier_achat.date() - client.date_premier_achat.date()).days
            jours_activite = max(jours_activite, 1)
        else:
            jours_activite = 1
        
        frequence_achat = (client.nombre_commandes / jours_activite) * 30  # Achats par mois
        
        data = {
            'client': ClientSerializer(client, context={'request': request}).data,
            'statistiques': {
                'demandes': {
                    'total': stats['total_demandes'],
                    'en_attente': stats['demandes_en_attente'],
                    'confirmees': stats['demandes_confirmees'],
                    'expediees': stats['demandes_expediees'],
                    'livrees': stats['demandes_livrees'],
                },
                'financieres': {
                    'montant_total': float(stats['montant_total']),
                    'panier_moyen': float(client.moyenne_panier),
                    'dernier_achat': client.date_dernier_achat,
                    'premier_achat': client.date_premier_achat,
                    'jours_activite': jours_activite,
                    'frequence_achat': round(frequence_achat, 2)
                },
                'fidelite': {
                    'points': client.points_fidelite,
                    'est_fidele': client.est_fidele,
                    'niveau': 'Fidèle' if client.est_fidele else 'Nouveau'
                }
            }
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def ajouter_points(self, request, pk=None):
        """Ajouter des points de fidélité à un client avec historisation"""
        client = self.get_object()
        points = request.data.get('points')
        raison = request.data.get('raison', '')
        
        if not points:
            raise ValidationError({'points': 'Le nombre de points est requis'})
        
        try:
            points = int(points)
            if points <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise ValidationError({'points': 'Le nombre de points doit être un entier positif'})
        
        anciens_points = client.points_fidelite
        
        # ✅ LOG: Historisation des points
        logger.info(
            f"Ajustement points - Client: {client.code_client}, "
            f"Anciens: {anciens_points}, Nouveaux: {anciens_points + points}, "
            f"Ajout: {points}, Raison: {raison}, "
            f"Utilisateur: {request.user}"
        )
        
        client.ajouter_points_fidelite(points)
        
        return Response({
            'status': 'success',
            'message': f'{points} points ajoutés au client',
            'client': {
                'id': client.id,
                'nom_complet': client.nom_complet,
                'anciens_points': anciens_points,
                'nouveaux_points': client.points_fidelite
            },
            'details': {
                'points': points,
                'raison': raison,
                'date': timezone.now(),
                'utilisateur': request.user.username if request.user.is_authenticated else None
            }
        })

# ========================================
# VIEWSETS DEMANDES
# ========================================

class DemandeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des demandes"""
    queryset = Demande.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DemandeFilter
    search_fields = ['numero', 'client__nom', 'client__prenom', 'client__email', 'numero_suivi']
    ordering_fields = ['numero', 'date_creation', 'montant_total_ttc', 'statut']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DemandeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DemandeUpdateSerializer
        return DemandeSerializer
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que leurs propres demandes
        if not self.request.user.is_staff:
            # On suppose que le client est lié à l'utilisateur par email
            queryset = queryset.filter(client__email=self.request.user.email)
        
        return queryset.select_related('client').prefetch_related('lignes', 'lignes__sticker')
    
    def perform_create(self, serializer):
        """Sauvegarder en spécifiant l'utilisateur connecté"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirmer(self, request, pk=None):
        """Confirmer une demande (passer de brouillon à confirmée)"""
        demande = self.get_object()
        
        if demande.statut != 'brouillon':
            raise ValidationError('Seules les demandes brouillon peuvent être confirmées')
        
        try:
            demande.confirmer()
            
            # ✅ LOG: Confirmation de demande
            logger.info(
                f"Confirmation demande - Demande: {demande.numero}, "
                f"Client: {demande.client.code_client}, "
                f"Montant: {demande.montant_total_ttc}, "
                f"Utilisateur: {request.user}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Demande confirmée avec succès',
                'demande': DemandeSerializer(demande, context={'request': request}).data
            })
        except Exception as e:
            logger.error(f"Erreur confirmation demande {demande.numero}: {str(e)}")
            raise ValidationError(str(e))
    
    @action(detail=True, methods=['post'])
    def expedier(self, request, pk=None):
        """Marquer une demande comme expédiée"""
        demande = self.get_object()
        transporteur = request.data.get('transporteur')
        numero_suivi = request.data.get('numero_suivi')
        
        if not transporteur:
            raise ValidationError({'transporteur': 'Le transporteur est requis'})
        
        if demande.statut != 'confirmee':
            raise ValidationError('Seules les demandes confirmées peuvent être expédiées')
        
        try:
            demande.expedier(transporteur, numero_suivi)
            
            # ✅ LOG: Expédition de demande
            logger.info(
                f"Expédition demande - Demande: {demande.numero}, "
                f"Transporteur: {transporteur}, Suivi: {numero_suivi}, "
                f"Utilisateur: {request.user}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Demande marquée comme expédiée',
                'demande': DemandeSerializer(demande, context={'request': request}).data
            })
        except Exception as e:
            logger.error(f"Erreur expédition demande {demande.numero}: {str(e)}")
            raise ValidationError(str(e))
    
    @action(detail=True, methods=['post'])
    def ajouter_paiement(self, request, pk=None):
        """Ajouter un paiement à une demande"""
        demande = self.get_object()
        montant = request.data.get('montant')
        mode_paiement = request.data.get('mode_paiement')
        
        if not montant or not mode_paiement:
            raise ValidationError({
                'montant': 'Le montant est requis',
                'mode_paiement': 'Le mode de paiement est requis'
            })
        
        try:
            montant = Decimal(str(montant))
            if montant <= 0:
                raise ValueError
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError({'montant': 'Le montant doit être un nombre positif'})
        
        # Mettre à jour le montant payé
        demande.montant_paye += montant
        
        # Mettre à jour le statut de paiement
        if demande.montant_paye >= demande.montant_total_ttc:
            demande.statut_paiement = 'paye'
            demande.date_paiement = timezone.now().date()
        elif demande.montant_paye > 0:
            demande.statut_paiement = 'partiel'
        
        demande.save()
        
        # ✅ LOG: Ajout de paiement
        logger.info(
            f"Paiement demande - Demande: {demande.numero}, "
            f"Montant: {montant}, Mode: {mode_paiement}, "
            f"Reste à payer: {demande.montant_restant}, "
            f"Utilisateur: {request.user}"
        )
        
        return Response({
            'status': 'success',
            'message': f'Paiement de {montant} € enregistré',
            'demande': DemandeSerializer(demande, context={'request': request}).data,
            'details': {
                'montant': float(montant),
                'mode_paiement': mode_paiement,
                'montant_restant': float(demande.montant_restant),
                'est_soldee': demande.est_soldee
            }
        })
    
    @action(detail=False, methods=['get'])
    def suivi(self, request):
        """Suivi des demandes pour le client connecté"""
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentification requise')
        
        # On suppose que le client est lié à l'utilisateur par email
        queryset = self.get_queryset().filter(client__email=request.user.email)
        
        # Filtrer par statut si spécifié
        statut = request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Trier par date de création décroissante
        queryset = queryset.order_by('-date_creation')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

# ========================================
# VIEWSETS FACTURES
# ========================================

class VentesFactureViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet en lecture seule pour les factures"""
    queryset = VentesFacture.objects.all()
    serializer_class = VentesFactureSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VentesFactureFilter
    search_fields = ['numero', 'client__nom', 'client__prenom', 'client__email']
    ordering_fields = ['numero', 'date_emission', 'montant_ttc', 'statut']
    ordering = ['-date_emission']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que leurs propres factures
        if not self.request.user.is_staff:
            queryset = queryset.filter(client__email=self.request.user.email)
        
        return queryset.select_related('client', 'demande')
    
    @action(detail=True, methods=['post'])
    def emettre(self, request, pk=None):
        """Émettre une facture"""
        facture = self.get_object()
        
        if facture.statut != 'brouillon':
            raise ValidationError('Seules les factures brouillon peuvent être émises')
        
        try:
            facture.emettre()
            
            # ✅ LOG: Émission de facture
            logger.info(
                f"Émission facture - Facture: {facture.numero}, "
                f"Client: {facture.client.code_client}, "
                f"Montant: {facture.montant_ttc}, "
                f"Utilisateur: {request.user}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Facture émise avec succès',
                'facture': VentesFactureSerializer(facture, context={'request': request}).data
            })
        except Exception as e:
            logger.error(f"Erreur émission facture {facture.numero}: {str(e)}")
            raise ValidationError(str(e))
    
    @action(detail=True, methods=['post'])
    def enregistrer_paiement(self, request, pk=None):
        """Enregistrer un paiement sur une facture"""
        facture = self.get_object()
        montant = request.data.get('montant')
        date_paiement = request.data.get('date_paiement')
        
        if not montant:
            raise ValidationError({'montant': 'Le montant est requis'})
        
        try:
            montant = Decimal(str(montant))
            if montant <= 0:
                raise ValueError
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError({'montant': 'Le montant doit être un nombre positif'})
        
        # Convertir la date si fournie
        paiement_date = None
        if date_paiement:
            try:
                paiement_date = parse_date_safe(date_paiement)
            except ValueError:
                raise ValidationError({'date_paiement': 'Format de date invalide. Utiliser YYYY-MM-DD'})
        
        # ✅ Vérifier que le paiement ne dépasse pas le montant restant
        montant_restant = facture.montant_restant
        if montant > montant_restant:
            raise ValidationError(
                {'montant': f'Montant trop élevé. Reste à payer: {montant_restant} €'}
            )
        
        facture.enregistrer_paiement(montant, paiement_date)
        
        # ✅ LOG: Enregistrement de paiement
        logger.info(
            f"Paiement facture - Facture: {facture.numero}, "
            f"Montant: {montant}, Date: {paiement_date}, "
            f"Nouveau reste: {facture.montant_restant}, "
            f"Utilisateur: {request.user}"
        )
        
        return Response({
            'status': 'success',
            'message': f'Paiement de {montant} € enregistré',
            'facture': VentesFactureSerializer(facture, context={'request': request}).data,
            'details': {
                'montant': float(montant),
                'montant_restant': float(facture.montant_restant),
                'est_payee': facture.statut == 'payee'
            }
        })

# ========================================
# VIEWSETS PAIEMENTS
# ========================================

class PaiementViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des paiements"""
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaiementFilter
    search_fields = ['reference', 'client__nom', 'client__prenom', 'client__email']
    ordering_fields = ['reference', 'date_paiement', 'montant']
    ordering = ['-date_paiement']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaiementCreateSerializer
        return PaiementSerializer
    
    def get_permissions(self):
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ: Seuls les admins peuvent gérer les paiements
    
    def perform_create(self, serializer):
        """Sauvegarder en spécifiant l'utilisateur connecté"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def par_periode(self, request):
        """Paiements groupés par période"""
        periode = request.query_params.get('periode', 'jour')  # jour, semaine, mois, annee
        
        queryset = self.get_queryset()
        
        if periode == 'jour':
            queryset = queryset.annotate(periode=TruncDate('date_paiement'))
        elif periode == 'mois':
            queryset = queryset.annotate(periode=TruncMonth('date_paiement'))
        elif periode == 'annee':
            queryset = queryset.annotate(periode=TruncYear('date_paiement'))
        else:  # semaine
            # Pour simplifier, on utilise le jour
            queryset = queryset.annotate(periode=TruncDate('date_paiement'))
        
        stats = queryset.values('periode').annotate(
            total=Coalesce(Sum('montant'), Decimal('0')),
            nombre=Count('id'),
            moyen=Coalesce(Avg('montant'), Decimal('0'))
        ).order_by('-periode')[:30]  # 30 dernières périodes
        
        return Response(stats)

# ========================================
# VIEWSETS PANIER
# ========================================

class PanierViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des paniers"""
    queryset = Panier.objects.all()
    serializer_class = PanierSerializer
    pagination_class = StandardPagination
    
    def get_permissions(self):
        if self.action in ['create', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que leur propre panier
        if not self.request.user.is_staff:
            # On suppose que le client est lié à l'utilisateur par email
            queryset = queryset.filter(client__email=self.request.user.email)
        
        return queryset.prefetch_related('items', 'items__sticker')
    
    @action(detail=True, methods=['post'])
    def ajouter_item(self, request, pk=None):
        """Ajouter un item au panier avec VERROUILLAGE"""
        from django.db import transaction
        
        panier = self.get_object()
        sticker_id = request.data.get('sticker_id')
        quantite = request.data.get('quantite', 1)
        texte_personnalise = request.data.get('texte_personnalise', '')
        couleur_personnalisee = request.data.get('couleur_personnalisee', '')
        
        if not sticker_id:
            raise ValidationError({'sticker_id': "L'ID du sticker est requis"})
        
        try:
            # ✅ VERROUILLAGE: Utiliser select_for_update pour éviter les problèmes de concurrence
            with transaction.atomic():
                sticker = VentesSticker.objects.select_for_update().get(
                    id=sticker_id, 
                    actif=True
                )
        except VentesSticker.DoesNotExist:
            raise ValidationError({'sticker_id': 'Sticker non trouvé ou inactif'})
        
        try:
            quantite = int(quantite)
            if quantite <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise ValidationError({'quantite': 'La quantité doit être un entier positif'})
        
        # ✅ Vérifier le stock AVEC VERROUILLAGE
        if sticker.quantite < quantite:
            raise ValidationError({
                'quantite': f'Stock insuffisant. Disponible: {sticker.quantite}'
            })
        
        # Ajouter ou mettre à jour l'item
        item, created = ItemPanier.objects.update_or_create(
            panier=panier,
            sticker=sticker,
            defaults={
                'quantite': quantite,
                'texte_personnalise': texte_personnalise,
                'couleur_personnalisee': couleur_personnalisee
            }
        )
        
        # Mettre à jour la date de modification du panier
        panier.save()
        
        # ✅ LOG: Ajout au panier
        logger.info(
            f"Ajout panier - Panier: {panier.id}, "
            f"Sticker: {sticker.code}, Quantité: {quantite}, "
            f"Utilisateur: {request.user}"
        )
        
        return Response({
            'status': 'success',
            'message': 'Item ajouté au panier',
            'item': ItemPanierSerializer(item, context={'request': request}).data,
            'panier': PanierSerializer(panier, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def retirer_item(self, request, pk=None):
        """Retirer un item du panier"""
        panier = self.get_object()
        item_id = request.data.get('item_id')
        
        if not item_id:
            raise ValidationError({'item_id': "L'ID de l'item est requis"})
        
        try:
            item = ItemPanier.objects.get(id=item_id, panier=panier)
            
            # ✅ LOG: Retrait du panier
            logger.info(
                f"Retrait panier - Panier: {panier.id}, "
                f"Sticker: {item.sticker.code}, Quantité: {item.quantite}, "
                f"Utilisateur: {request.user}"
            )
            
            item.delete()
            
            # Mettre à jour la date de modification du panier
            panier.save()
            
            return Response({
                'status': 'success',
                'message': 'Item retiré du panier',
                'panier': PanierSerializer(panier, context={'request': request}).data
            })
        except ItemPanier.DoesNotExist:
            raise ValidationError({'item_id': 'Item non trouvé dans le panier'})
    
    @action(detail=True, methods=['post'])
    def vider(self, request, pk=None):
        """Vider le panier"""
        panier = self.get_object()
        
        # ✅ LOG: Vidage du panier
        logger.info(
            f"Vidage panier - Panier: {panier.id}, "
            f"Nombre d'items: {panier.items.count()}, "
            f"Utilisateur: {request.user}"
        )
        
        panier.vider()
        
        return Response({
            'status': 'success',
            'message': 'Panier vidé',
            'panier': PanierSerializer(panier, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def passer_commande(self, request, pk=None):
        """Passer une commande à partir du panier"""
        from django.db import transaction
        
        panier = self.get_object()
        
        if not panier.items.exists():
            raise ValidationError({'panier': 'Le panier est vide'})
        
        # ✅ VERROUILLAGE: Utiliser une transaction atomique
        with transaction.atomic():
            # Vérifier le stock pour tous les items AVANT de créer la commande
            for item in panier.items.all():
                sticker = VentesSticker.objects.select_for_update().get(id=item.sticker.id)
                if sticker.quantite < item.quantite:
                    raise ValidationError({
                        'stock': f'Stock insuffisant pour {sticker.nom}. '
                                 f'Disponible: {sticker.quantite}, Demandé: {item.quantite}'
                    })
            
            # Créer une demande à partir du panier
            demande_data = {
                'client': panier.client.id,
                'mode_livraison': request.data.get('mode_livraison', 'standard'),
                'adresse_livraison': request.data.get('adresse_livraison', ''),
                'mode_paiement': request.data.get('mode_paiement', ''),
                'notes_client': request.data.get('notes_client', ''),
                'lignes': []
            }
            
            # Créer les lignes de demande à partir des items du panier
            for item in panier.items.all():
                ligne_data = {
                    'sticker': item.sticker.id,
                    'quantite': item.quantite,
                    'texte_personnalise': item.texte_personnalise,
                    'couleur_personnalisee': item.couleur_personnalisee
                }
                demande_data['lignes'].append(ligne_data)
            
            serializer = DemandeCreateSerializer(
                data=demande_data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                demande = serializer.save()
                
                # ✅ LOG: Commande passée
                logger.info(
                    f"Commande passée - Panier: {panier.id}, "
                    f"Demande: {demande.numero}, "
                    f"Nombre d'items: {panier.items.count()}, "
                    f"Utilisateur: {request.user}"
                )
                
                # Vider le panier après la commande
                panier.vider()
                
                return Response({
                    'status': 'success',
                    'message': 'Commande passée avec succès',
                    'demande': DemandeSerializer(demande, context={'request': request}).data,
                    'panier': PanierSerializer(panier, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ========================================
# VIEWSETS AVIS CLIENTS
# ========================================

class AvisClientViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des avis clients"""
    queryset = AvisClient.objects.all()
    serializer_class = AvisClientSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AvisClientFilter
    search_fields = ['titre', 'commentaire', 'client__nom', 'client__prenom', 'sticker__nom']
    ordering_fields = ['created_at', 'note', 'utile_oui']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'mes_avis']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'retrieve', 'par_sticker']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        
        # Pour le public, ne montrer que les avis validés
        if not self.request.user.is_staff:
            queryset = queryset.filter(est_valide=True, est_modere=True)
        
        return queryset.select_related('client', 'sticker', 'commande')
    
    def perform_create(self, serializer):
        """Sauvegarder en spécifiant le client connecté"""
        # ✅ CORRECTION: Utiliser ValidationError de DRF
        from rest_framework.exceptions import ValidationError
        
        # On suppose que le client est lié à l'utilisateur par email
        try:
            client = Client.objects.get(email=self.request.user.email)
            serializer.save(client=client)
            
            # ✅ LOG: Création d'avis
            logger.info(
                f"Avis créé - Client: {client.code_client}, "
                f"Sticker: {serializer.instance.sticker.code}, "
                f"Note: {serializer.instance.note}"
            )
        except Client.DoesNotExist:
            raise ValidationError("Client non trouvé")
    
    @action(detail=False, methods=['get'])
    def mes_avis(self, request):
        """Avis du client connecté"""
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentification requise')
        
        queryset = self.get_queryset().filter(client__email=request.user.email)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_sticker(self, request, sticker_id=None):
        """Avis pour un sticker spécifique"""
        if sticker_id:
            queryset = self.get_queryset().filter(sticker_id=sticker_id)
        else:
            sticker_id = request.query_params.get('sticker_id')
            if not sticker_id:
                raise ValidationError({'sticker_id': "L'ID du sticker est requis"})
            queryset = self.get_queryset().filter(sticker_id=sticker_id)
        
        # Statistiques optimisées
        stats = queryset.aggregate(
            moyenne=Coalesce(Avg('note'), Decimal('0')),
            total=Count('id'),
            utile=Coalesce(Sum('utile_oui'), 0),
            inutile=Coalesce(Sum('utile_non'), 0)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response({
                'stats': {
                    'moyenne': float(stats['moyenne']),
                    'total': stats['total'],
                    'utile': stats['utile'],
                    'inutile': stats['inutile'],
                    'pourcentage_utile': (
                        (stats['utile'] / max(stats['utile'] + stats['inutile'], 1)) * 100
                        if stats['utile'] + stats['inutile'] > 0 else 0
                    )
                },
                'avis': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            'stats': {
                'moyenne': float(stats['moyenne']),
                'total': stats['total'],
                'utile': stats['utile'],
                'inutile': stats['inutile'],
                'pourcentage_utile': (
                    (stats['utile'] / max(stats['utile'] + stats['inutile'], 1)) * 100
                    if stats['utile'] + stats['inutile'] > 0 else 0
                )
            },
            'avis': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def marquer_utile(self, request, pk=None):
        """Marquer un avis comme utile"""
        avis = self.get_object()
        
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentification requise')
        
        # Vérifier que l'utilisateur n'a pas déjà voté
        # Vous pourriez stocker les votes dans une table séparée
        
        avis.utile_oui += 1
        avis.save()
        
        return Response({
            'status': 'success',
            'message': 'Avis marqué comme utile',
            'avis': AvisClientSerializer(avis, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def marquer_inutile(self, request, pk=None):
        """Marquer un avis comme inutile"""
        avis = self.get_object()
        
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentification requise')
        
        avis.utile_non += 1
        avis.save()
        
        return Response({
            'status': 'success',
            'message': 'Avis marqué comme inutile',
            'avis': AvisClientSerializer(avis, context={'request': request}).data
        })

# ========================================
# VIEWSETS CODES PROMO
# ========================================

class CodePromoViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des codes promo"""
    queryset = CodePromo.objects.all()
    serializer_class = CodePromoSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_reduction', 'est_actif']
    search_fields = ['code', 'description']
    ordering_fields = ['code', 'date_debut', 'date_fin']
    ordering = ['-date_debut']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'verifier']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]  # ✅ CORRIGÉ
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        
        # Pour le public, ne montrer que les codes actifs
        if not self.request.user.is_staff:
            queryset = queryset.filter(est_actif=True)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def verifier(self, request):
        """Vérifier la validité d'un code promo"""
        code = request.data.get('code')
        client_id = request.data.get('client_id')
        montant_panier = request.data.get('montant_panier', 0)
        
        if not code:
            raise ValidationError({'code': 'Le code promo est requis'})
        
        try:
            code_promo = CodePromo.objects.get(code=code)
        except CodePromo.DoesNotExist:
            raise ValidationError({'code': 'Code promo non trouvé'})
        
        # Récupérer le client si fourni
        client = None
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                pass
        
        # Vérifier la validité
        valide, message = code_promo.est_valide(client, Decimal(str(montant_panier)))
        
        if not valide:
            return Response({
                'valide': False,
                'message': message,
                'code': code
            })
        
        # Calculer la réduction
        reduction = code_promo.appliquer_reduction(Decimal(str(montant_panier)))
        
        return Response({
            'valide': True,
            'message': message,
            'code': CodePromoSerializer(code_promo, context={'request': request}).data,
            'reduction': float(reduction),
            'montant_apres_reduction': float(Decimal(str(montant_panier)) - reduction)
        })
    
    @action(detail=True, methods=['post'])
    def utiliser(self, request, pk=None):
        """Enregistrer une utilisation du code promo"""
        code_promo = self.get_object()
        
        # Vérifier la validité
        valide, message = code_promo.est_valide()
        
        if not valide:
            raise ValidationError({'code': message})
        
        # ✅ LOG: Utilisation du code promo
        logger.info(
            f"Utilisation code promo - Code: {code_promo.code}, "
            f"Utilisations actuelles: {code_promo.utilisations_actuelles}, "
            f"Utilisateur: {request.user}"
        )
        
        code_promo.utiliser()
        
        return Response({
            'status': 'success',
            'message': 'Code promo utilisé avec succès',
            'code': CodePromoSerializer(code_promo, context={'request': request}).data,
            'utilisations_restantes': (
                code_promo.utilisations_max - code_promo.utilisations_actuelles
                if code_promo.utilisations_max else None
            )
        })

# ========================================
# VUES STATISTIQUES
# ========================================

class StatistiquesAPIView(APIView):
    """API pour les statistiques"""
    permission_classes = [permissions.IsAdminUser]  # ✅ CORRIGÉ: IsAdminUser sans parenthèses est correct pour une classe
    
    def get(self, request):
        periode = request.query_params.get('periode', 'mois')  # jour, semaine, mois, annee
        date_debut_str = request.query_params.get('date_debut')
        date_fin_str = request.query_params.get('date_fin')
        
        # ✅ CORRECTION: Gestion sécurisée des dates
        today = timezone.now().date()
        
        # Définir la période par défaut
        if periode == 'jour':
            date_debut = parse_date_safe(date_debut_str, today)
            date_fin = parse_date_safe(date_fin_str, today)
        elif periode == 'semaine':
            date_debut = parse_date_safe(date_debut_str, today - timedelta(days=7))
            date_fin = parse_date_safe(date_fin_str, today)
        elif periode == 'mois':
            date_debut = parse_date_safe(date_debut_str, today.replace(day=1))
            date_fin = parse_date_safe(date_fin_str, today)
        elif periode == 'annee':
            date_debut = parse_date_safe(date_debut_str, today.replace(month=1, day=1))
            date_fin = parse_date_safe(date_fin_str, today)
        else:
            date_debut = parse_date_safe(date_debut_str, today - timedelta(days=30))
            date_fin = parse_date_safe(date_fin_str, today)
        
        # Convertir en datetime pour les requêtes
        date_debut_dt = timezone.make_aware(
            datetime.combine(date_debut, datetime.min.time())
        )
        date_fin_dt = timezone.make_aware(
            datetime.combine(date_fin, datetime.max.time())
        )
        
        # Statistiques des ventes
        demandes = Demande.objects.filter(
            date_creation__range=[date_debut_dt, date_fin_dt]
        )
        
        stats_ventes = demandes.aggregate(
            nombre_commandes=Coalesce(Count('id'), 0),
            chiffre_affaires_ht=Coalesce(Sum('sous_total_ht'), Decimal('0')),
            chiffre_affaires_ttc=Coalesce(Sum('montant_total_ttc'), Decimal('0')),
            stickers_vendus=Coalesce(Sum('lignes__quantite'), 0)
        )
        
        # Statistiques clients
        nouveaux_clients = Client.objects.filter(
            created_at__range=[date_debut_dt, date_fin_dt]
        ).count()
        
        clients_actifs = Client.objects.filter(
            date_dernier_achat__range=[date_debut_dt, date_fin_dt],
            est_actif=True
        ).count()
        
        # Panier moyen
        panier_moyen = Decimal('0')
        if stats_ventes['nombre_commandes'] > 0:
            panier_moyen = (
                stats_ventes['chiffre_affaires_ttc'] / 
                stats_ventes['nombre_commandes']
            )
        
        # Top stickers
        top_stickers = LigneDemande.objects.filter(
            demande__date_creation__range=[date_debut_dt, date_fin_dt]
        ).values(
            'sticker__id', 'sticker__code', 'sticker__nom'
        ).annotate(
            total_vendu=Coalesce(Sum('quantite'), 0),
            chiffre_affaires=Coalesce(Sum('montant_ttc'), Decimal('0'))
        ).order_by('-total_vendu')[:10]
        
        # Top clients
        top_clients = Client.objects.filter(
            demandes__date_creation__range=[date_debut_dt, date_fin_dt]
        ).annotate(
            total_achats=Coalesce(Sum('demandes__montant_total_ttc'), Decimal('0')),
            nombre_commandes=Count('demandes')
        ).order_by('-total_achats')[:10]
        
        data = {
            'periode': {
                'debut': date_debut.isoformat(),
                'fin': date_fin.isoformat(),
                'type': periode
            },
            'ventes': {
                'nombre_commandes': stats_ventes['nombre_commandes'],
                'chiffre_affaires_ht': float(stats_ventes['chiffre_affaires_ht']),
                'chiffre_affaires_ttc': float(stats_ventes['chiffre_affaires_ttc']),
                'stickers_vendus': stats_ventes['stickers_vendus'],
                'panier_moyen': float(panier_moyen)
            },
            'clients': {
                'nouveaux': nouveaux_clients,
                'actifs': clients_actifs
            },
            'top_stickers': list(top_stickers),
            'top_clients': [
                {
                    'id': c.id,
                    'nom_complet': c.nom_complet,
                    'total_achats': float(c.total_achats),
                    'nombre_commandes': c.nombre_commandes
                }
                for c in top_clients
            ]
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)

# ========================================
# VUES PUBLIC
# ========================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def catalogue_stickers(request):
    """Catalogue public des stickers"""
    queryset = VentesSticker.objects.filter(actif=True)
    
    # Filtres
    categorie = request.query_params.get('categorie')
    type_sticker = request.query_params.get('type_sticker')
    materiau = request.query_params.get('materiau')
    prix_min = request.query_params.get('prix_min')
    prix_max = request.query_params.get('prix_max')
    search = request.query_params.get('search')
    
    if categorie:
        queryset = queryset.filter(categorie=categorie)
    if type_sticker:
        queryset = queryset.filter(type_sticker=type_sticker)
    if materiau:
        queryset = queryset.filter(materiau=materiau)
    if prix_min:
        queryset = queryset.filter(prix_ttc__gte=prix_min)
    if prix_max:
        queryset = queryset.filter(prix_ttc__lte=prix_max)
    if search:
        queryset = queryset.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search) |
            Q(categorie__icontains=search)
        )
    
    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    result_page = paginator.paginate_queryset(queryset, request)
    
    serializer = VentesStickerMinimalSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def detail_sticker(request, pk):
    """Détail public d'un sticker"""
    try:
        sticker = VentesSticker.objects.get(id=pk, actif=True)
    except VentesSticker.DoesNotExist:
        return Response(
            {'error': 'Sticker non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = VentesStickerSerializer(sticker, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def contact_commercial(request):
    """Formulaire de contact commercial"""
    nom = request.data.get('nom')
    email = request.data.get('email')
    telephone = request.data.get('telephone')
    message = request.data.get('message')
    sujet = request.data.get('sujet', 'Demande de contact')
    
    if not all([nom, email, message]):
        return Response(
            {'error': 'Nom, email et message sont requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ✅ LOG: Contact commercial
    logger.info(
        f"Contact commercial - Nom: {nom}, Email: {email}, "
        f"Sujet: {sujet}, Téléphone: {telephone}"
    )
    
    # Ici, vous pourriez envoyer un email ou sauvegarder dans la base de données
    
    return Response({
        'status': 'success',
        'message': 'Message envoyé avec succès. Nous vous contacterons bientôt.'
    })

# ========================================
# VUES UTILISATEUR
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mon_compte(request):
    """Informations du compte de l'utilisateur connecté"""
    try:
        client = Client.objects.get(email=request.user.email)
    except Client.DoesNotExist:
        return Response(
            {'error': 'Compte client non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ClientSerializer(client, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def modifier_compte(request):
    """Modifier les informations du compte"""
    try:
        client = Client.objects.get(email=request.user.email)
    except Client.DoesNotExist:
        return Response(
            {'error': 'Compte client non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ClientCreateSerializer(client, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        #  LOG: Modification de compte
        logger.info(
            f"Modification compte - Client: {client.code_client}, "
            f"Utilisateur: {request.user}"
        )
        
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ========================================
# VUES RAPIDES
# ========================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def stats_rapides(request):
    """Statistiques rapides pour l'accueil"""
    total_stickers = VentesSticker.objects.filter(actif=True).count()
    stickers_en_stock = VentesSticker.objects.filter(actif=True, quantite__gt=0).count()
    total_clients = Client.objects.filter(est_actif=True).count()
    demandes_du_jour = Demande.objects.filter(
        date_creation__date=timezone.now().date()
    ).count()
    
    return Response({
        'stickers': {
            'total': total_stickers,
            'en_stock': stickers_en_stock
        },
        'clients': {
            'total': total_clients
        },
        'commandes': {
            'aujourd_hui': demandes_du_jour
        }
    })