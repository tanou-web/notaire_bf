# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class VentesSticker(models.Model):
    code = models.CharField(unique=True, max_length=50)
    type_sticker = models.CharField(max_length=50, blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantite = models.IntegerField()
    actif = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ventes_sticker'
        db_table_comment = 'Pour suivi des ventes stickers selon section 3.1.f du cahier'


class VentesFacture(models.Model):
    numero = models.CharField(unique=True, max_length=50)
    demande = models.ForeignKey('DemandesDemande', models.DO_NOTHING)
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2)
    tva = models.DecimalField(max_digits=10, decimal_places=2)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2)
    fichier_pdf = models.CharField(max_length=200, blank=True, null=True)
    date_emission = models.DateField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ventes_facture'
