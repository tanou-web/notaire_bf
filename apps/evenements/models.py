from django.db import models
from django.utils import timezone

class Evenement(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    lieu = models.CharField(max_length=200)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='evenements/', blank=True, null=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'evenements_evenement'
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'

    def __str__(self):
        return self.titre


class Inscription(models.Model):
    QUALITE_CHOICES = [
        ('notaire', 'Notaire'),
        ('collaborateur', 'Collaborateur de notaire'),
        ('autre', 'Autre (à préciser)'),
    ]

    STATUT_PAIEMENT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='inscriptions')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    nationalite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, verbose_name="Téléphone / WhatsApp")
    email = models.EmailField()
    qualite = models.CharField(max_length=20, choices=QUALITE_CHOICES)
    autre_qualite = models.CharField(max_length=100, blank=True, null=True)
    
    date_arrivee = models.DateField()
    heure_arrivee = models.TimeField()
    plan_vol = models.FileField(upload_to='evenements/plans_vol/', blank=True, null=True)
    
    statut_paiement = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='en_attente')
    justificatif_paiement = models.FileField(upload_to='evenements/justificatifs/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'evenements_inscription'
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.evenement}"
