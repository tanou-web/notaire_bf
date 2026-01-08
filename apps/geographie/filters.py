# apps/geographie/filters.py
import django_filters
from .models import GeographieVille

class VilleFilter(django_filters.FilterSet):
    region_code = django_filters.CharFilter(field_name='region__code', lookup_expr='exact')

    class Meta:
        model = GeographieVille
        fields = ['region', 'region_code', 'nom', 'code_postal']  # tu peux ajouter d'autres champs si besoin
