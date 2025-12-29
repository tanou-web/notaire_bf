from rest_framework import viewsets, filters, status, permissions
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import DemandesDemande, DemandesPieceJointe
from .serializers import (
    DemandeSerializer, DemandeCreateSerializer,
    PieceJointeSerializer, PieceJointeCreateSerializer
)
from apps.utilisateurs.permissions import IsOwnerOrReadOnly

class DemandeViewSet(viewsets.ModelViewSet):
    queryset = DemandesDemande.objects.all()
    serializer_class = DemandeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'document', 'notaire']
    search_fields = ['reference', 'email_reception']
    ordering_fields = ['created_at', 'updated_at', 'montant_total']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return DemandesDemande.objects.all()
        if user.is_authenticated:
            return DemandesDemande.objects.filter(utilisateur=user)
        return DemandesDemande.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DemandeCreateSerializer
        return super().get_serializer_class()
    
    @action(detail=True, methods=['post'])
    def assigner_notaire(self, request, pk=None):
        demande = self.get_object()
        notaire_id = request.data.get('notaire_id')
        
        # Logique d'assignation
        from apps.notaires.models import NotairesNotaire
        try:
            notaire = NotairesNotaire.objects.get(id=notaire_id, actif=True)
            demande.notaire = notaire
            demande.date_attribution = timezone.now()
            demande.statut = 'en_traitement'
            demande.save()
            
            return Response({
                'status': 'success',
                'message': f'Notaire {notaire.nom} assigné à la demande',
                'demande': DemandeSerializer(demande).data
            })
        except NotairesNotaire.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Notaire non trouvé ou inactif'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def completer_traitement(self, request, pk=None):
        demande = self.get_object()
        document_genere = request.FILES.get('document_genere')

        if not document_genere:
            return Response({
                'error': 'Le document généré est requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Store filename/path — storage handling can be improved later
        demande.document_genere = getattr(document_genere, 'name', str(document_genere))
        demande.statut = 'document_envoye_email'
        demande.date_envoi_email = timezone.now()
        demande.save()
        
        # Envoyer l'email (simplifié)
        # TODO: Implémenter l'envoi d'email réel
        
        return Response({
            'status': 'success',
            'message': 'Document envoyé par email',
            'demande': DemandeSerializer(demande).data
        })


class PieceJointeViewSet(viewsets.ModelViewSet):
    """API pour les pièces jointes des demandes"""
    queryset = DemandesPieceJointe.objects.all()
    serializer_class = PieceJointeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['demande', 'type_piece']
    ordering_fields = ['created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PieceJointeCreateSerializer
        return PieceJointeSerializer

    def get_permissions(self):
        if self.action == 'create':
            return []  # autorise tout le monde pour créer
        return [permission() for permission in self.permission_classes]

    
    def get_queryset(self):
        user = self.request.user
        # Les utilisateurs voient seulement les pièces jointes de leurs demandes
        if user.is_superuser or user.is_staff:
            return DemandesPieceJointe.objects.all()
        return DemandesPieceJointe.objects.filter(demande__utilisateur=user)

    
    def perform_create(self, serializer):
        demande_id = serializer.validated_data.get('demande')
        if not demande_id:
            raise serializers.ValidationError({'demande': 'La demande est requise'})
        
        try:
            demande = DemandesDemande.objects.get(id=demande_id.id if hasattr(demande_id, 'id') else demande_id)
        except DemandesDemande.DoesNotExist:
            raise serializers.ValidationError({'demande': 'Demande introuvable'})
        
        # Vérifier que l'utilisateur peut ajouter des pièces à cette demande
        if not self.request.user.is_staff and demande.utilisateur not in [self.request.user, None]:
            raise permissions.PermissionDenied("Vous ne pouvez pas ajouter de pièce jointe à cette demande")
        serializer.save()