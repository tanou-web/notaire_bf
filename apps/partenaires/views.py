from rest_framework import viewsets, permissions, filters
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import PartenairesPartenaire
from .serializers import PartenaireSerializer


class PartenaireViewSet(viewsets.ModelViewSet):
    """API for partenaires.

    - list/retrieve: public
    - create/update/destroy: admin only
    Supports filtering by `actif` and ordering by `ordre`.
    """
    queryset = PartenairesPartenaire.objects.all().order_by('ordre')
    serializer_class = PartenaireSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['actif', 'type_partenaire']
    search_fields = ['nom', 'type_partenaire']
    ordering_fields = ['ordre', 'nom']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        now = timezone.now()
        serializer.save(created_at=now, updated_at=now)

    def perform_update(self, serializer):
        serializer.save(updated_at=timezone.now())
