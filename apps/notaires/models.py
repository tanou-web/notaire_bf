# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class NotairesNotaire(models.Model):
    matricule = models.CharField(unique=True, max_length=50)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    photo = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=254)
    telephone = models.CharField(max_length=20)
    region = models.ForeignKey('GeographieRegion', models.DO_NOTHING, blank=True, null=True)
    ville = models.ForeignKey('GeographieVille', models.DO_NOTHING, blank=True, null=True)
    adresse = models.TextField()
    actif = models.BooleanField()
    total_ventes = models.DecimalField(max_digits=15, decimal_places=2)
    total_cotisations = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'notaires_notaire'


class NotairesCotisation(models.Model):
    notaire = models.ForeignKey(NotairesNotaire, models.DO_NOTHING)
    annee = models.IntegerField()
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20)
    date_paiement = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'notaires_cotisation'
        unique_together = (('notaire', 'annee'),)
