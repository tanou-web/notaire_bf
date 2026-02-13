# apps/ventes/views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
import uuid
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import VenteSticker, DemandeVente, Paiement, AvisClient, CodePromo, ReferenceSticker, VenteStickerNotaire
from apps.demandes.models import DemandesDemande
from .serializers import (
    VentesStickerSerializer, VenteStickerCreateSerializer,
    DemandeCreateSerializer, DemandeSerializer,
    AvisClientCreateSerializer, ReferenceStickerSerializer, 
    VenteStickerNotaireSerializer, RecuStickerSerializer, RecuStickerCreateSerializer
)

# ========================================
# 1. API VENTE DE STICKER (LIÉE À NOTAIRE)
# ========================================

class VenteStickerViewSet(viewsets.ViewSet):
    """
    API pour les ventes de stickers (liées à un notaire)
    """
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def creer(self, request):
        """
        Créer une vente de sticker
        POST /api/ventes-stickers/creer/
        """
        from .services import VenteStickerService
        
        try:
            result = VenteStickerService.creer_vente(
                data=request.data,
                request=request
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'reference': result['vente'].reference,
                    'sticker': result['vente'].sticker.nom,
                    'notaire': result['vente'].notaire.nom_complet,
                    'montant': float(result['vente'].montant_total)
                }
            }, status=201)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def par_notaire(self, request):
        """
        Ventes d'un notaire spécifique (admin)
        GET /api/ventes-stickers/par-notaire/?notaire_id=<id>
        """
        notaire_id = request.query_params.get('notaire_id')

        if not notaire_id:
            raise ValidationError({'notaire_id': 'ID notaire requis'})

        try:
            # Vérifier que le notaire existe
            from apps.notaires.models import NotairesNotaire
            notaire = NotairesNotaire.objects.get(id=notaire_id)
        except NotairesNotaire.DoesNotExist:
            raise ValidationError({'notaire_id': 'Notaire non trouvé'})
        except Exception as e:
            raise ValidationError({'notaire_id': f'Erreur de vérification notaire: {str(e)}'})

        try:
            ventes = VenteSticker.objects.filter(
                notaire_id=notaire_id
            ).select_related('sticker', 'notaire').order_by('-date_vente')

            data = []
            for v in ventes:
                try:
                    # Vérifier que sticker existe et a un nom
                    sticker_nom = v.sticker.nom if v.sticker and hasattr(v.sticker, 'nom') else "Sticker inconnu"

                    vente_data = {
                        'reference': v.reference or "N/A",
                        'sticker': sticker_nom,
                        'client': v.client_nom or "Client anonyme",
                        'quantite': v.quantite or 0,
                        'montant': float(v.montant_total or 0),
                        'date': v.date_vente.isoformat() if v.date_vente else None,
                        'statut': v.get_statut_display() if hasattr(v, 'get_statut_display') else v.statut
                    }
                    data.append(vente_data)

                except Exception as e:
                    # Log l'erreur pour cette vente spécifique mais continue
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Erreur traitement vente {v.id}: {str(e)}")
                    continue

            return Response({
                'notaire': {
                    'id': notaire.id,
                    'nom': f"{notaire.nom} {notaire.prenom}",
                    'matricule': notaire.matricule
                },
                'ventes': data,
                'total_ventes': len(data)
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur récupération ventes notaire {notaire_id}: {str(e)}")
            raise ValidationError({'detail': f'Erreur interne: {str(e)}'})


# ========================================
# 2. API DEMANDE DOCUMENT (LIÉE À NOTAIRE)
# ========================================

class DemandeViewSet(viewsets.ViewSet):
    """
    API pour les demandes de documents
    """
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def creer(self, request):
        """
        Créer une demande de document
        POST /api/demandes/creer/
        """
        from .services import DemandeService
        
        try:
            result = DemandeService.creer_demande_sans_compte(
                data=request.data,
                request=request
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'reference': result['demande'].reference,
                    'token': str(result['demande'].token_acces),
                    'lien_suivi': result['demande'].lien_suivi,
                    'document': result['demande'].document.nom,
                    'montant': float(result['demande'].montant_total)
                }
            }, status=201)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)


# ========================================
# 3. API PAIEMENT (COMMUN)
# ========================================

class PaiementViewSet(viewsets.ViewSet):
    """
    API pour les paiements (demandes + ventes stickers)
    """
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def initier(self, request):
        """
        Initier un paiement
        POST /api/paiements/initier/
        """
        type_transaction = request.data.get('type_transaction')  # 'demande' ou 'vente_sticker'
        reference = request.data.get('reference')  # Réf demande ou vente
        
        if not type_transaction or not reference:
            raise ValidationError({
                'type_transaction': 'Type requis',
                'reference': 'Référence requise'
            })
        
        from .services import PaiementService
        
        try:
            result = PaiementService.initier_paiement(
                type_transaction=type_transaction,
                reference=reference,
                type_paiement=request.data.get('type_paiement'),
                request=request
            )
            
            return Response({
                'status': 'success',
                'paiement': {
                    'reference': result['paiement'].reference,
                    'montant': float(result['paiement'].montant),
                    'statut': result['paiement'].statut
                },
                'payment_url': result.get('payment_url')
            })
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)


# ========================================
# 4. API CATALOGUE STICKERS
# ========================================

class ReferenceStickerViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les types de stickers disponibles (Admin)
    """
    queryset = ReferenceSticker.objects.all()
    serializer_class = ReferenceStickerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class VenteStickerNotaireViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les ventes de stickers aux notaires
    """
    queryset = VenteStickerNotaire.objects.all().select_related('notaire', 'type_sticker')
    serializer_class = VenteStickerNotaireSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['notaire', 'type_sticker']
    search_fields = ['reference', 'plage_debut', 'plage_fin', 'notaire__nom']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def par_notaire(self, request):
        """
        Liste des ventes pour un notaire spécifique
        """
        notaire_id = request.query_params.get('notaire_id')
        if not notaire_id:
            return Response({"error": "notaire_id est requis"}, status=400)
        
        ventes = self.get_queryset().filter(notaire_id=notaire_id)
        serializer = self.get_serializer(ventes, many=True)
        return Response(serializer.data)

class VentesStickerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API catalogue des stickers (lecture seule)
    """
    queryset = VenteSticker.objects.all()
    serializer_class = VentesStickerSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['get'])
    def notaires_vendeurs(self, request, pk=None):
        """
        Notaires qui ont vendu ce sticker
        GET /api/ventes/stickers/<id>/notaires-vendeurs/
        """
        sticker = self.get_object()

        notaires = VenteSticker.objects.filter(
            sticker=sticker
        ).values(
            'notaire__id',
            'notaire__nom',
            'notaire__prenom',
            'notaire__email'
        ).distinct()

        return Response(list(notaires))

    @action(detail=False, methods=['get'])
    def get_notaires_vendeurs(self, request):
        """
        Notaires qui ont vendu un sticker spécifique (via query param)
        GET /api/ventes/stickers/get-notaires-vendeurs/?sticker_id=<id>
        """
        sticker_id = request.query_params.get('sticker_id')

        if not sticker_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'sticker_id': 'ID sticker requis'})

        try:
            from apps.documents.models import DocumentsDocument
            sticker = DocumentsDocument.objects.get(id=sticker_id)
        except DocumentsDocument.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Sticker non trouvé')

        notaires = VenteSticker.objects.filter(
            sticker=sticker
        ).values(
            'notaire__id',
            'notaire__nom',
            'notaire__prenom',
            'notaire__email'
        ).distinct()

        # Reformater les données pour des noms de champs plus propres
        formatted_notaires = [
            {
                'id': notaire['notaire__id'],
                'nom': notaire['notaire__nom'],
                'prenom': notaire['notaire__prenom'],
                'email': notaire['notaire__email']
            }
            for notaire in notaires
        ]

        return Response({
            'results': formatted_notaires
        })


# ========================================
# 5. API STATISTIQUES NOTAIRES (ADMIN)
# ========================================

class StatistiquesNotairesAPIView(APIView):
    """
    Statistiques globales des ventes pour le dashboard
    Retourne les agrégats globaux attendus par le frontend
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Count, Sum, Q
        from datetime import timedelta

        periode = request.query_params.get('periode', '30j')
        date_fin = timezone.now().date()
        
        if periode == '7j':
            date_debut = date_fin - timedelta(days=7)
        elif periode == '30j':
            date_debut = date_fin - timedelta(days=30)
        elif periode == '90j':
            date_debut = date_fin - timedelta(days=90)
        else:
            date_debut = date_fin - timedelta(days=30)

        nom_sticker = request.query_params.get('nom_sticker')

        # Filtres de base
        filtres_ventes = Q(date_vente__date__gte=date_debut)
        filtres_ventes_notaires = Q(date_vente__date__gte=date_debut)

        if nom_sticker:
            filtres_ventes &= Q(sticker__nom__icontains=nom_sticker)
            filtres_ventes_notaires &= Q(type_sticker__nom__icontains=nom_sticker)

        # Agrégats des ventes de stickers aux clients (via notaires)
        ventes_clients = VenteSticker.objects.filter(filtres_ventes).aggregate(
            total_stickers=Sum('quantite'),
            total_ventes=Count('id'),
            revenu_total=Sum('montant_total')
        )

        # Agrégats des ventes de stickers aux notaires (stock)
        ventes_notaires_stock = VenteStickerNotaire.objects.filter(filtres_ventes_notaires).aggregate(
            total_stickers=Sum('quantite'),
            total_ventes=Count('id'),
            revenu_total=Sum('montant_total')
        )

        # Valeurs par défaut
        v_client_qty = ventes_clients.get('total_stickers') or 0
        v_client_count = ventes_clients.get('total_ventes') or 0
        v_client_revenue = ventes_clients.get('revenu_total') or 0

        v_notaire_qty = ventes_notaires_stock.get('total_stickers') or 0
        v_notaire_count = ventes_notaires_stock.get('total_ventes') or 0
        v_notaire_revenue = ventes_notaires_stock.get('revenu_total') or 0

        # Statistiques des demandes (uniquement si pas de filtre par nom de sticker ou si pertinent)
        demandes_stats = {}
        if not nom_sticker:
            demandes_stats = DemandeVente.objects.filter(
                created_at__gte=date_debut
            ).aggregate(
                total_demandes=Count('id'),
                demandes_terminees=Count('id', filter=Q(statut='terminee'))
            )

        return Response({
            'periode': {
                'debut': date_debut,
                'fin': date_fin,
                'label': periode
            },
            'filtre_nom': nom_sticker,
            'ventes_clients': {
                'quantite': v_client_qty,
                'nombre_transactions': v_client_count,
                'revenu': float(v_client_revenue)
            },
            'ventes_notaires': {
                'quantite': v_notaire_qty,
                'nombre_transactions': v_notaire_count,
                'revenu': float(v_notaire_revenue)
            },
            'total_global': {
                'quantite': v_client_qty + v_notaire_qty,
                'revenu_total': float(v_client_revenue + v_notaire_revenue)
            },
            'demandes_total': demandes_stats.get('total_demandes') or 0,
            'demandes_terminees': demandes_stats.get('demandes_terminees') or 0
        })

class RecuStickerViewSet(viewsets.ModelViewSet):
    """
    API pour la génération et la récupération des reçus de stickers
    """
    queryset = VenteStickerNotaire.objects.all().select_related('notaire', 'type_sticker')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return RecuStickerCreateSerializer
        return RecuStickerSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return VenteStickerNotaire.objects.all().select_related('notaire', 'type_sticker')
        return VenteStickerNotaire.objects.all().select_related('notaire', 'type_sticker')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vente = serializer.save()
        
        # Retourner le format de reçu spécifique
        response_serializer = RecuStickerSerializer(vente)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        """
        Générer le PDF du reçu (Future implémentation)
        """
        recu = self.get_object()
        # Logique de génération PDF ici
        return Response({'status': 'PDF generation not implemented yet'})
