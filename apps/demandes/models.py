# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone
from django.conf import settings

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
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='demandes',
        verbose_name="Utilisateur"
    )
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


class DemandesPieceJointe(models.Model):
    """Pièces jointes pour les demandes (CNIB, PDF, etc.)"""
    TYPE_PIECE_CHOICES = [
        ('cnib', 'CNIB (Carte Nationale d\'Identité Burkinabé)'),
        ('passeport', 'Passeport'),
        ('document_identite', 'Autre document d\'identité'),
        ('document_legal', 'Document légal'),
        ('autre', 'Autre document'),
    ]
    
    demande = models.ForeignKey(
        DemandesDemande,
        on_delete=models.CASCADE,
        related_name='pieces_jointes',
        verbose_name="Demande"
    )
    type_piece = models.CharField(
        max_length=30,
        choices=TYPE_PIECE_CHOICES,
        verbose_name="Type de pièce"
    )
    fichier = models.FileField(
        upload_to='demandes/pieces_jointes/%Y/%m/',
        verbose_name="Fichier",
        help_text="Format accepté: PDF, JPG, PNG (max 10MB)"
    )
    nom_original = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nom original du fichier"
    )
    taille_fichier = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Taille du fichier (octets)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'demandes_piecejointe'
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.demande.reference} - {self.get_type_piece_display()}"
    
    def save(self, *args, **kwargs):
        # Enregistrer le nom original et la taille lors de la sauvegarde
        if self.fichier and not self.nom_original:
            self.nom_original = self.fichier.name
        if self.fichier and not self.taille_fichier:
            try:
                self.taille_fichier = self.fichier.size
            except:
                pass
        super().save(*args, **kwargs)
    
    @property
    def taille_formatee(self):
        """Retourne la taille formatée (KB, MB)"""
        if not self.taille_fichier:
            return "0 B"
        taille = self.taille_fichier
        for unit in ['B', 'KB', 'MB', 'GB']:
            if taille < 1024.0:
                return f"{taille:.2f} {unit}"
            taille /= 1024.0
        return f"{taille:.2f} TB"