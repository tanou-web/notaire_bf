from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titre', 'contenu', 'auteur']
    ordering_fields = ['date', 'created_at', 'titre']
    ordering = ['-date']

    def get_queryset(self):
        """Support du paramètre 'q' pour la recherche générale"""
        queryset = super().get_queryset()

        # Support du paramètre 'q' pour la recherche générale
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(titre__icontains=search_query) |
                Q(contenu__icontains=search_query) |
                Q(auteur__icontains=search_query)
            )

        return queryset

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
