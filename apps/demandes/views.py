from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import DemandesDemande
from .serializers import DemandeSerializer, DemandeCreateSerializer
from apps.utilisateurs.permissions import IsOwnerOrReadOnly

class DemandeViewSet(viewsets.ModelViewSet):
    queryset = DemandesDemande.objects.all()
    serializer_class = DemandeSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'document', 'notaire']
    search_fields = ['reference', 'email_reception']
    ordering_fields = ['created_at', 'updated_at', 'montant_total']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return DemandesDemande.objects.all()
        return DemandesDemande.objects.filter(utilisateur=user)
    
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