import django_filters
from .models import DemandesDemande

class DemandeFilter(django_filters.FilterSet):
    date_min = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_max = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    montant_min = django_filters.NumberFilter(field_name='montant_total', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant_total', lookup_expr='lte')
    
    class Meta:
        model = DemandesDemande
        fields = ['statut', 'document', 'notaire', 'utilisateur']