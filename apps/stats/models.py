from tabnanny import verbose
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import MaxValueValidator

class StatsVisite(models.Model):
    """Modèle pour stocker les statistiques de visites quotidiennes."""
    
    date = models.DateField(
        unique=True,
        verbose_name=_("Date"),
        help_text=_("Date de la statistique")
    )
    
    visites = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Nombre de visites"),
        help_text=_("Nombre total de visites uniques")
    )
    
    pages_vues = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Pages vues"),
        help_text=_("Nombre total de pages consultées")
    )
    
    visites_authentifiees = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Visites authentifiées"),
        help_text=_("Visites de utilisateurs connectés")
    )
    
    duree_moyenne = models.FloatField(
        default=0.0,
        verbose_name=_("Durée moyenne (en minutes)"),
        help_text=_("Temps moyen passé sur le site")
    )
    
    taux_rebond = models.FloatField(
        default=0.0,
        verbose_name=_("Taux de rebond (%)"),
        help_text=_("Pourcentage de visites avec une seule page vue")
    )
    
    heure = models.IntegerField(
        verbose_name=_('Heure (0-23)'),
        validators= [MinValueValidator(0), MaxValueValidator(23)]
    )
    # Sources de trafic
    trafic_direct = models.IntegerField(default=0, verbose_name=_("Trafic direct"))
    trafic_reference = models.IntegerField(default=0, verbose_name=_("Trafic référent"))
    trafic_recherche = models.IntegerField(default=0, verbose_name=_("Trafic recherche"))
    trafic_social = models.IntegerField(default=0, verbose_name=_("Trafic réseaux sociaux"))
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Dernière mise à jour")
    )
    
    class Meta:
        managed = True  # Changé à True pour que Django gère la table
        db_table = 'stats_visite'
        verbose_name = _("Statistique de visite")
        verbose_name_plural = _("Statistiques de visites")
        ordering = ['-date']  # Tri par date décroissante par défaut
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(visites__gte=0),
                name='visites_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(pages_vues__gte=0),
                name='pages_vues_positive'
            ),
            models.CheckConstraint(
                condition=models.Q(taux_rebond__gte=0) & models.Q(taux_rebond__lte=100),
                name='taux_rebond_valide'
            ),
        ]
    
    def __str__(self):
        return f"Statistiques du {self.date} - {self.visites} visites"
    
    @property
    def pages_par_visite(self):
        """Calcule le nombre moyen de pages par visite."""
        if self.visites > 0:
            return round(self.pages_vues / self.visites, 2)
        return 0
    
    @property
    def duree_totale(self):
        """Calcule la durée totale passée sur le site."""
        return round(self.duree_moyenne * self.visites, 2)
    
    @property
    def trafic_total(self):
        """Calcule le trafic total de toutes sources."""
        return (
            self.trafic_direct + 
            self.trafic_reference + 
            self.trafic_recherche + 
            self.trafic_social
        )
    
    @property
    def jour_semaine(self):
        """Retourne le jour de la semaine en français."""
        jours = [
            'Lundi', 'Mardi', 'Mercredi', 'Jeudi',
            'Vendredi', 'Samedi', 'Dimanche'
        ]
        return jours[self.date.weekday()]
    
    @property
    def est_weekend(self):
        """Détermine si la date est un weekend."""
        return self.date.weekday() >= 5  # 5 = Samedi, 6 = Dimanche
    
    def calculer_taux_rebond(self):
        """Calcule le taux de rebond si non fourni."""
        if self.visites > 0:
            # Simuler un calcul basique (à adapter selon vos données)
            visites_une_page = int(self.visites * 0.4)  # Exemple: 40% de rebond
            return round((visites_une_page / self.visites) * 100, 2)
        return 0
    
    def save(self, *args, **kwargs):
        """Override de la méthode save pour calculs automatiques."""
        # Calcul automatique du taux de rebond si non défini
        if not self.taux_rebond and self.visites > 0:
            self.taux_rebond = self.calculer_taux_rebond()
        
        # Vérifier la cohérence des données
        if self.pages_vues > 0 and self.visites == 0:
            # Si des pages ont été vues, il y a au moins une visite
            self.visites = 1
        
        super().save(*args, **kwargs)
    
    @classmethod
    def obtenir_ou_creer_pour_date(cls, date):
        """Obtient ou crée une entrée pour une date spécifique."""
        obj, created = cls.objects.get_or_create(
            date=date,
            defaults={
                'visites': 0,
                'pages_vues': 0,
            }
        )
        return obj, created
    
    @classmethod
    def statistiques_periode(cls, date_debut, date_fin):
        """Calcule les statistiques agrégées pour une période."""
        stats = cls.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).aggregate(
            total_visites=models.Sum('visites'),
            total_pages_vues=models.Sum('pages_vues'),
            moyenne_duree=models.Avg('duree_moyenne'),
            moyenne_taux_rebond=models.Avg('taux_rebond'),
        )
        
        return {
            'periode': f"{date_debut} à {date_fin}",
            'jours': (date_fin - date_debut).days + 1,
            'visites_total': stats['total_visites'] or 0,
            'pages_vues_total': stats['total_pages_vues'] or 0,
            'visites_moyennes': round((stats['total_visites'] or 0) / ((date_fin - date_debut).days + 1), 2),
            'pages_par_visite': round(
                (stats['total_pages_vues'] or 0) / (stats['total_visites'] or 1), 2
            ),
            'duree_moyenne': round(stats['moyenne_duree'] or 0, 2),
            'taux_rebond_moyen': round(stats['moyenne_taux_rebond'] or 0, 2),
        }
    
class PageVue(models.Model):
    """Statistiques par page individuelle."""
    
    date = models.DateField(verbose_name=_("Date"))
    url = models.CharField(max_length=500, verbose_name=_("URL"))
    titre = models.CharField(max_length=200, blank=True, verbose_name=_("Titre"))
    vues = models.IntegerField(default=0, verbose_name=_("Nombre de vues"))
    temps_moyen = models.FloatField(default=0.0, verbose_name=_("Temps moyen (secondes)"))
    
    class Meta:
        db_table = 'stats_page_vue'
        unique_together = ['date', 'url']
        verbose_name = _("Statistique de page")
        verbose_name_plural = _("Statistiques de pages")
        indexes = [
            models.Index(fields=['date', 'url']),
            models.Index(fields=['-vues']),
        ]
    
    def __str__(self):
        return f"{self.titre or self.url} - {self.date}"


class Referent(models.Model):
    """Sources de référents (sites qui envoient du trafic)."""
    
    date = models.DateField(verbose_name=_("Date"))
    domaine = models.CharField(max_length=200, verbose_name=_("Domaine"))
    url = models.CharField(max_length=500, verbose_name=_("URL complète"))
    visites = models.IntegerField(default=0, verbose_name=_("Visites"))
    
    class Meta:
        db_table = 'stats_referent'
        unique_together = ['date', 'domaine']
        verbose_name = _("Référent")
        verbose_name_plural = _("Référents")
    
    def __str__(self):
        return f"{self.domaine} - {self.visites} visites"


class PaysVisite(models.Model):
    """Statistiques géographiques."""
    
    date = models.DateField(verbose_name=_("Date"))
    pays = models.CharField(max_length=100, verbose_name=_("Pays"))
    code_pays = models.CharField(max_length=2, verbose_name=_("Code pays"))
    visites = models.IntegerField(default=0, verbose_name=_("Visites"))
    
    class Meta:
        db_table = 'stats_pays'
        unique_together = ['date', 'pays']
        verbose_name = _("Visite par pays")
        verbose_name_plural = _("Visites par pays")
    
    def __str__(self):
        return f"{self.pays} - {self.visites} visites"


class PeriodeActive(models.Model):
    """Heures et jours d'activité."""
    
    date = models.DateField(verbose_name=_("Date"))
    heure = models.IntegerField(verbose_name=_("Heure (0-23)"))
    visites = models.IntegerField(default=0, verbose_name=_("Visites"))
    
    class Meta:
        db_table = 'stats_periode_active'
        unique_together = ['date', 'heure']
        verbose_name = _("Période active")
        verbose_name_plural = _("Périodes actives")
    
    def __str__(self):
        return f"{self.date} {self.heure}h - {self.visites} visites"
