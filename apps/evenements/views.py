from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Evenement, Inscription
from .serializers import EvenementSerializer, InscriptionSerializer

class EvenementViewSet(viewsets.ModelViewSet):
    """API pour la gestion des événements"""
    queryset = Evenement.objects.filter(actif=True)
    serializer_class = EvenementSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titre', 'lieu']
    ordering_fields = ['date_debut', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    # apps/evenements/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Evenement

@api_view(['GET'])
def evenement_choices(request):
    STATUT_CHOICES = [choice[0] for choice in Evenement.STATUT_CHOICES]
    return Response({'statuts': STATUT_CHOICES})


class InscriptionViewSet(viewsets.ModelViewSet):
    """API pour les inscriptions aux événements"""
    queryset = Inscription.objects.all()
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Logique additionnelle lors de l'inscription
        serializer.save()
