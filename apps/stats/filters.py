# apps/stats/filters.py
import django_filters
from .models import StatsVisite
from django.contrib.auth import get_user_model

User = get_user_model()

class StatsVisiteFilter(django_filters.FilterSet):
    # Exemple de filtre calculé
    est_weekend = django_filters.BooleanFilter(method='filter_est_weekend')
    # Exemple pour un champ lié
    utilisateur = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = StatsVisite
        fields = ['date', 'est_weekend', 'utilisateur']  # seulement les vrais champs

    def filter_est_weekend(self, queryset, name, value):
        if value:
            return queryset.filter(date__week_day__in=[1,7])
        return queryset.exclude(date__week_day__in=[1,7])
