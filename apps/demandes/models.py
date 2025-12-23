# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DemandesDemande(models.Model):
    reference = models.CharField(unique=True, max_length=50)
    utilisateur = models.ForeignKey('UtilisateursUser', models.DO_NOTHING)
    document = models.ForeignKey('DocumentsDocument', models.DO_NOTHING)
    statut = models.CharField(max_length=50)
    donnees_formulaire = models.JSONField()
    email_reception = models.CharField(max_length=254, blank=True, null=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    frais_commission = models.DecimalField(max_digits=10, decimal_places=2)
    notaire = models.ForeignKey('NotairesNotaire', models.DO_NOTHING, blank=True, null=True)
    date_attribution = models.DateTimeField(blank=True, null=True)
    document_genere = models.CharField(max_length=200, blank=True, null=True)
    date_envoi_email = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'demandes_demande'
        db_table_comment = 'Workflow strict: brouillon → attente_formulaire → attente_paiement → en_attente_traitement → en_traitement → document_envoye_email'
