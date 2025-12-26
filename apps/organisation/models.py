# apps/organisation/models.py
from django.db import models

class OrganisationMembrebureau(models.Model):
    POSTE_CHOICES = [
        ('president', 'Président'),
        ('vice_president', 'Vice-Président'),
        ('secretaire', 'Secrétaire'),
        ('secretaire_adjoint', 'Secrétaire Adjoint'),
        ('tresorier', 'Trésorier'),
        ('tresorier_adjoint', 'Trésorier Adjoint'),
        ('conseiller', 'Conseiller'),
        ('membre', 'Membre'),
    ]
    
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    poste = models.CharField(max_length=100, choices=POSTE_CHOICES)
    photo = models.ImageField(upload_to='membres_bureau/', blank=True, null=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Informations supplémentaires
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    biographie = models.TextField(blank=True, null=True)
    date_entree = models.DateField(blank=True, null=True)
    date_sortie = models.DateField(blank=True, null=True)
    mandat_debut = models.DateField(blank=True, null=True)
    mandat_fin = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'organisation_membrebureau'
        verbose_name = 'Membre du Bureau'
        verbose_name_plural = 'Membres du Bureau'
        ordering = ['ordre', 'nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.get_poste_display()}"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"
    
    @property
    def est_en_mandat(self):
        """Vérifie si le membre est actuellement en mandat"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.mandat_debut and self.mandat_fin:
            return self.mandat_debut <= today <= self.mandat_fin
        return self.actif