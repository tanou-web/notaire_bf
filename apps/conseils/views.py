from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import ConseilsConseildujour
from .serializers import ConseilDuJourSerializer


class ConseilsViewSet(viewsets.ModelViewSet):
    """API for Conseil du jour.

    - list/retrieve: AllowAny
    - create/update/destroy: IsAdminUser
    """
    queryset = ConseilsConseildujour.objects.all().order_by('-date')
    serializer_class = ConseilDuJourSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        now = timezone.now()
        # set created_at and updated_at to now to avoid DB NOT NULL errors
        serializer.save(created_at=now, updated_at=now)

    def perform_update(self, serializer):
        # update updated_at timestamp
        serializer.save(updated_at=timezone.now())
