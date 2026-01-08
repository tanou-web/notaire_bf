# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class CommunicationsEmaillog(models.Model):
    type_email = models.CharField(max_length=50)
    destinataire = models.CharField(max_length=254)
    sujet = models.CharField(max_length=200)
    contenu = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ('envoye', 'Envoyé'),
        ('echec', 'Échec'),
        ('ouvert', 'Ouvert'),
        ('clique', 'Cliqué'),
    ]
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message_id = models.CharField(max_length=200, blank=True, null=True)
    erreur = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    public_reference = models.CharField(max_length=50,null=True,blank=True)
    class Meta:
        managed = True
        db_table = 'communications_emaillog'
        indexes = [
            models.Index(fields=['destinataire']),
            models.Index(fields=['sujet']),
            models.Index(fields=['statut']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]


class CommunicationsSmslog(models.Model):
    destinataire = models.CharField(max_length=20, help_text="Numéro de téléphone du destinataire")
    message = models.TextField(help_text="Contenu du SMS")
    fournisseur = models.CharField(max_length=50, help_text="Fournisseur SMS utilisé (aqilas, orange, moov)")
    sender_id = models.CharField(max_length=20, blank=True, null=True, help_text="ID de l'expéditeur")

    STATUS_CHOICES = [
        ('envoye', 'Envoyé'),
        ('echec', 'Échec'),
        ('en_attente', 'En attente'),
        ('delivre', 'Livré'),
        ('non_delivre', 'Non délivré'),
    ]
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')

    message_id = models.CharField(max_length=200, blank=True, null=True, help_text="ID du message retourné par l'API")
    erreur = models.TextField(blank=True, null=True, help_text="Message d'erreur en cas d'échec")
    cout_sms = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Coût du SMS en FCFA")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    public_reference = models.CharField(max_length=50, null=True, blank=True, help_text="Référence publique pour tracking")

    class Meta:
        managed = True
        db_table = 'communications_smslog'
        indexes = [
            models.Index(fields=['destinataire']),
            models.Index(fields=['statut']),
            models.Index(fields=['fournisseur']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"SMS vers {self.destinataire} - {self.statut}"