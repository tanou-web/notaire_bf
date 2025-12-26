# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.utils import timezone
from django.db import models


class NotairesNotaire(models.Model):
    matricule = models.CharField(unique=True, max_length=50)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    photo = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    region = models.ForeignKey('geographie.GeographieRegion', on_delete=models.SET_NULL, blank=True, null=True)
    ville = models.ForeignKey('geographie.GeographieVille', on_delete=models.SET_NULL,blank=True, null=True)
    adresse = models.TextField()
    actif = models.BooleanField(default=True)
    total_ventes = models.DecimalField(max_digits=15, decimal_places=2,default=0)
    total_cotisations = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'notaires_notaire'

    def __str__(self):
        return f'{self.nom}  {self.prenom}'


class NotairesCotisation(models.Model):
    notaire = models.ForeignKey(NotairesNotaire, on_delete=models.CASCADE, related_name='cotisations')
    annee = models.PositiveIntegerField()
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(
        max_length=20,
        choices=[
            ('payee','Payée'),
            ('impayee', 'Impayée')
        ],
        default='impayee'        
    )
    date_paiement = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'notaires_cotisation'
        unique_together = (('notaire', 'annee'),)
    def __str__(self):
        return f'{self.notaire} - {self.annee}'
