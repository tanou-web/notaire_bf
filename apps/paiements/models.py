# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class PaiementsTransaction(models.Model):
    reference = models.CharField(unique=True, max_length=100)
    demande = models.OneToOneField('DemandesDemande', models.DO_NOTHING)
    type_paiement = models.CharField(max_length=20)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, db_comment='3% selon cahier des charges pour API paiement')
    statut = models.CharField(max_length=20)
    donnees_api = models.JSONField()
    date_creation = models.DateTimeField()
    date_maj = models.DateTimeField()
    date_validation = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paiements_transaction'
