from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Evenement, Inscription, EvenementChamp
from .serializers import (
    EvenementSerializer,
    InscriptionSerializer,
    InscriptionCreateSerializer
)


class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.filter(actif=True)
    serializer_class = EvenementSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Permettre aux admins de voir tous les événements, y compris inactifs"""
        queryset = Evenement.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(actif=True)
        return queryset

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def formulaire(self, request, pk=None):
        evenement = self.get_object()
        champs = EvenementChamp.objects.filter(
            evenement=evenement,
            actif=True
        ).order_by('ordre')

        return Response({
            "evenement": evenement.id,
            "formulaire": [
                {
                    "id": c.id,
                    "label": c.label,
                    "type": c.type,
                    "obligatoire": c.obligatoire,
                    "options": c.options
                }
                for c in champs
            ]
        })


class InscriptionViewSet(viewsets.ModelViewSet):
    queryset = Inscription.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return InscriptionCreateSerializer
        return InscriptionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Evenement

@api_view(['GET'])
def evenement_choices(request):
    choices = Evenement.objects.values_list('id', 'titre')
    return Response(list(choices))
