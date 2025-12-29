# apps/stats/services.py
from django.db import models
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from .models import (
    StatsVisite,    
    PageVue,        
    Referent,       
    PaysVisite,     
    PeriodeActive   
)

logger = logging.getLogger(__name__)

class StatsService:
    """Service pour gérer les statistiques de visites."""
    
    @staticmethod
    def incrementer_visite(date=None, pages_vues=1, authentifie=False):
        """Incrémente les compteurs de visites pour une date."""
        if date is None:
            date = timezone.now().date()
        
        try:
            stats, created = StatsVisite.objects.get_or_create(
                date=date,
                defaults={
                    'visites': 1,
                    'pages_vues': pages_vues,
                    'visites_authentifiees': 1 if authentifie else 0,
                }
            )
            
            if not created:
                stats.visites = models.F('visites') + 1
                stats.pages_vues = models.F('pages_vues') + pages_vues
                if authentifie:
                    stats.visites_authentifiees = models.F('visites_authentifiees') + 1
                stats.save(update_fields=[
                    'visites', 'pages_vues', 'visites_authentifiees', 'updated_at'
                ])
            
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de l'incrément des stats: {e}")
            return None
    
    @staticmethod
    def obtenir_tendances(nb_jours=30):
        """Obtient les tendances sur N jours."""
        date_fin = timezone.now().date()
        date_debut = date_fin - timedelta(days=nb_jours)
        
        stats = StatsVisite.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).order_by('date')
        
        # Calculer les tendances
        tendances = []
        for stat in stats:
            tendances.append({
                'date': stat.date,
                'visites': stat.visites,
                'pages_vues': stat.pages_vues,
                'pages_par_visite': stat.pages_par_visite,
                'jour_semaine': stat.jour_semaine,
                'est_weekend': stat.est_weekend,
            })
        
        return tendances
    
    @staticmethod
    def generer_rapport_mensuel(mois=None, annee=None):
        """Génère un rapport mensuel complet."""
        if mois is None:
            mois = timezone.now().month
        if annee is None:
            annee = timezone.now().year
        
        date_debut = timezone.datetime(annee, mois, 1).date()
        if mois == 12:
            date_fin = timezone.datetime(annee + 1, 1, 1).date() - timedelta(days=1)
        else:
            date_fin = timezone.datetime(annee, mois + 1, 1).date() - timedelta(days=1)
        
        stats_jours = StatsVisite.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        )
        
        # Agrégations
        aggregates = stats_jours.aggregate(
            total_visites=Sum('visites'),
            total_pages=Sum('pages_vues'),
            moyenne_visites=Avg('visites'),
            moyenne_pages_par_visite=Avg('pages_vues') / Avg('visites'),
            jours_avec_visites=Count('id'),
        )
        
        # Meilleur jour
        meilleur_jour = stats_jours.order_by('-visites').first()
        
        # Répartition weekend/semaine
        weekend_stats = stats_jours.filter(
            models.Q(date__week_day=1) | models.Q(date__week_day=7)  # Dimanche=1, Samedi=7
        ).aggregate(
            visites=Sum('visites'),
            jours=Count('id')
        )
        
        semaine_stats = stats_jours.exclude(
            models.Q(date__week_day=1) | models.Q(date__week_day=7)
        ).aggregate(
            visites=Sum('visites'),
            jours=Count('id')
        )
        
        return {
            'periode': f"{mois}/{annee}",
            'dates': f"{date_debut} - {date_fin}",
            'totaux': aggregates,
            'meilleur_jour': {
                'date': meilleur_jour.date if meilleur_jour else None,
                'visites': meilleur_jour.visites if meilleur_jour else 0,
            },
            'repartition': {
                'weekend': weekend_stats,
                'semaine': semaine_stats,
            },
            'jours': list(stats_jours.values('date', 'visites', 'pages_vues')),
        }