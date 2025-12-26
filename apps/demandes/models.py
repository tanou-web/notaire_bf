# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DemandesDemande(models.Model):
    STATUT_CHOICES = (
        ('brouillon', 'Brouillon'),
        ('attente_formulaire', 'Attente formulaire'),
        ('attente_paiement', 'Attente paiement'),
        ('en_attente_traitement', 'En attente traitement'),
        ('en_traitement', 'En traitement'),
        ('document_envoye_email', 'Document envoyé par email'),
        ('annule', 'Annulé'),
    )

    id = models.AutoField(primary_key=True)
    reference = models.CharField(max_length=50, unique=True, blank=True, null=True)
    utilisateur = models.ForeignKey('utilisateurs.UtilisateursUser', on_delete=models.CASCADE)
    document = models.ForeignKey('documents.DocumentsDocument', on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='brouillon')
    donnees_formulaire = models.JSONField(default=dict)
    email_reception = models.EmailField(max_length=254, blank=True, null=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    frais_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notaire = models.ForeignKey('notaires.NotairesNotaire', on_delete=models.SET_NULL, blank=True, null=True)
    date_attribution = models.DateTimeField(blank=True, null=True)
    document_genere = models.CharField(max_length=200, blank=True, null=True)
    date_envoi_email = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'demandes_demande'
        verbose_name = 'Demande'
        verbose_name_plural = 'Demandes'

    def __str__(self):
        return f"{self.reference or '-'} ({self.statut})"
