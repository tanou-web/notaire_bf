# apps/notaires/filters.py
import django_filters
from .models import NotairesNotaire

class NotaireFilter(django_filters.FilterSet):
    """Filtres avancés pour les notaires"""
    nom_complet = django_filters.CharFilter(method='filter_nom_complet')
    ventes_min = django_filters.NumberFilter(field_name='total_ventes', lookup_expr='gte')
    ventes_max = django_filters.NumberFilter(field_name='total_ventes', lookup_expr='lte')
    experience_min = django_filters.NumberFilter(field_name='annees_experience', lookup_expr='gte')
    experience_max = django_filters.NumberFilter(field_name='annees_experience', lookup_expr='lte')
    
    class Meta:
        model = NotairesNotaire
        fields = {
            'region': ['exact'],
            'ville': ['exact'],
            'actif': ['exact'],
            'specialites': ['contains'],
        }
    
    def filter_nom_complet(self, queryset, name, value):
        """Filtrer par nom complet (nom + prénom)"""
        return queryset.filter(
            Q(nom__icontains=value) | Q(prenom__icontains=value)
        )

# Ajouter dans la vue
from .filters import NotaireFilter

class NotaireViewSet(viewsets.ModelViewSet):
    # ...
    filterset_class = NotaireFilter  # Remplacer filterset_fields