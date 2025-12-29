# apps/ventes/views.py
from rest_framework import viewsets, status, permissions
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

from .models import VenteSticker, DemandeVente, Paiement, AvisClient, CodePromo

from .serializers import (
    VentesStickerSerializer, VenteStickerCreateSerializer,
    DemandeCreateSerializer, DemandeSerializer,
    AvisClientCreateSerializer
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
        
        ventes = VenteSticker.objects.filter(
            notaire_id=notaire_id
        ).select_related('sticker').order_by('-date_vente')
        
        data = [{
            'reference': v.reference,
            'sticker': v.sticker.nom,
            'client': v.client_nom,
            'quantite': v.quantite,
            'montant': float(v.montant_total),
            'date': v.date_vente
        } for v in ventes]
        
        return Response(data)


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
        GET /api/stickers/<id>/notaires-vendeurs/
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


# ========================================
# 5. API STATISTIQUES NOTAIRES (ADMIN)
# ========================================

class StatistiquesNotairesAPIView(APIView):
    """
    Statistiques par notaire (admin seulement)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        from django.db.models import Count, Sum
        from datetime import timedelta
        
        date_debut = timezone.now() - timedelta(days=30)
        
        # Statistiques ventes stickers par notaire
        stats_ventes = VenteSticker.objects.filter(
            date_vente__gte=date_debut
        ).values(
            'notaire__id',
            'notaire__nom',
            'notaire__prenom'
        ).annotate(
            total_ventes=Count('id'),
            total_montant=Sum('montant_total'),
            stickers_vendus=Sum('quantite')
        ).order_by('-total_montant')
        
        # Statistiques demandes par notaire
        stats_demandes = Demande.objects.filter(
            notaire__isnull=False,
            created_at__gte=date_debut
        ).values(
            'notaire__id',
            'notaire__nom',
            'notaire__prenom'
        ).annotate(
            total_demandes=Count('id'),
            demandes_terminees=Count('id', filter=Q(statut='termine')),
            total_montant=Sum('montant_total')
        ).order_by('-total_montant')
        
        return Response({
            'periode': {
                'debut': date_debut.date(),
                'fin': timezone.now().date()
            },
            'ventes_stickers': list(stats_ventes),
            'demandes_documents': list(stats_demandes)
        })