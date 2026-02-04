# apps/ventes/models.py - ORDRE CORRECT

import uuid
from decimal import Decimal
from datetime import timedelta

from django.db import models, transaction
from django.db.models import Q, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


# =====================================================
# FONCTIONS UTILITAIRES
# =====================================================

def token_expire_30j():
    return timezone.now() + timedelta(days=30)


def token_expire_7j():
    return timezone.now() + timedelta(days=7)


# =====================================================
# 1. CODE PROMO (d'abord car indépendant)
# =====================================================

class CodePromo(models.Model):
    code = models.CharField(max_length=50, unique=True)
    taux_reduction = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    actif = models.BooleanField(default=True)
    date_expiration = models.DateTimeField(null=True, blank=True)

    def est_valide(self):
        if not self.actif:
            return False
        if self.date_expiration and self.date_expiration < timezone.now():
            return False
        return True

    def __str__(self):
        return self.code


# =====================================================
# 2. REFERENCE STICKER (Catalogue pour Notaires)
# =====================================================

class ReferenceSticker(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom du sticker")
    description = models.TextField(verbose_name="Description", blank=True)
    image = models.ImageField(upload_to='stickers/references/', null=True, blank=True, verbose_name="Image du sticker")
    prix_unitaire = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prix Unitaire (FCFA)"
    )
    total_stock = models.PositiveIntegerField(default=0, verbose_name="Stock Total")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Référence Sticker"
        verbose_name_plural = "Références Stickers"

    def __str__(self):
        return self.nom


# =====================================================
# 3. VENTE STICKER NOTAIRE (Suivi avec Plages & Paiements)
# =====================================================

class VenteStickerNotaire(models.Model):
    reference = models.CharField(max_length=30, unique=True, blank=True)
    notaire = models.ForeignKey(
        'notaires.NotairesNotaire',
        on_delete=models.PROTECT,
        related_name='ventes_notaires'
    )
    type_sticker = models.ForeignKey(
        ReferenceSticker,
        on_delete=models.PROTECT,
        related_name='ventes'
    )
    
    quantite = models.PositiveIntegerField(verbose_name="Quantité")
    plage_debut = models.CharField(max_length=100, verbose_name="Plage de début (Ex: A1010101)")
    plage_fin = models.CharField(max_length=100, verbose_name="Plage de fin (Ex: A2000002)")
    
    montant_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Montant Total"
    )
    montant_paye = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Montant Payé"
    )
    reste_a_payer = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Reste à Payer"
    )
    
    date_vente = models.DateTimeField(default=timezone.now, verbose_name="Date de vente")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _generer_reference(self):
        return f"VNT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generer_reference()
        
        # Calcul automatique des montants
        if self.type_sticker:
            self.montant_total = self.type_sticker.prix_unitaire * self.quantite
        
        self.reste_a_payer = self.montant_total - self.montant_paye
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Vente Sticker Notaire"
        verbose_name_plural = "Ventes Stickers Notaires"
        ordering = ['-date_vente']

    def __str__(self):
        return f"{self.reference} - {self.notaire.nom_complet}"


# =====================================================
# 4. DEMANDE (quatrième car Paiement y fait référence)
# =====================================================

class DemandeVente(models.Model):
    STATUT_CHOICES = [
        ('en_attente', _('En attente')),
        ('en_traitement', _('En traitement')),
        ('terminee', _('Terminée')),
        ('rejetee', _('Rejetée')),
    ]

    reference = models.CharField(max_length=30, unique=True, blank=True)
    client_email = models.EmailField(db_index=True)
    notaire = models.ForeignKey(
        'notaires.NotairesNotaire',
        on_delete=models.SET_NULL,
        null=True,
        related_name='demandes'
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        db_index=True
    )

    montant_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    est_payee = models.BooleanField(default=False)

    token_acces = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    token_expire = models.DateTimeField(default=token_expire_30j)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _generer_reference(self):
        return f"DEM-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generer_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


# =====================================================
# 3. VENTE STICKER (troisième car Paiement y fait référence)
# =====================================================

class VenteSticker(models.Model):
    STATUT_CHOICES = [
        ('en_attente', _('En attente')),
        ('confirmee', _('Confirmée')),
        ('annulee', _('Annulée')),
    ]

    reference = models.CharField(max_length=30, unique=True, blank=True)
    sticker = models.ForeignKey(
        'documents.DocumentsDocument',
        on_delete=models.PROTECT,
        related_name='ventes_stickers'
    )
    
    code = models.CharField(max_length=50, unique=True)

    client_email = models.EmailField(db_index=True)
    notaire = models.ForeignKey(
        'notaires.NotairesNotaire',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ventes_stickers'
    )

    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    montant_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        db_index=True
    )

    est_payee = models.BooleanField(default=False)

    token_acces = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    token_expire = models.DateTimeField(default=token_expire_7j)

    date_vente = models.DateTimeField(default=timezone.now)

    def _generer_reference(self):
        return f"VEN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generer_reference()

        if self.montant_total == 0:
            self.montant_total = self.prix_unitaire * self.quantite

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference

# =====================================================
# 4. PAIEMENT (quatrième car il référence Demande et VenteSticker)
# =====================================================

class Paiement(models.Model):
    TYPE_PAIEMENT = [
        ('orange_money', 'Orange Money'),
        ('moov_money', 'Moov Money'),
    ]

    STATUT_CHOICES = [
        ('en_attente', _('En attente')),
        ('reussi', _('Réussi')),
        ('echoue', _('Échoué')),
    ]

    reference = models.CharField(max_length=30, unique=True, blank=True)

    demande = models.ForeignKey(
        'DemandeVente', 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='paiements'
    )

    vente_sticker = models.ForeignKey(
        VenteSticker,  
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='paiements'
    )

    type_paiement = models.CharField(max_length=20, choices=TYPE_PAIEMENT)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        db_index=True
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(demande__isnull=False) | Q(vente_sticker__isnull=False),
                name='paiement_demande_ou_vente'
            )
        ]

    def _generer_reference(self):
        return f"PAY-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generer_reference()

        if self.statut == 'reussi' and not self.date_validation:
            self.date_validation = timezone.now()

            with transaction.atomic():
                if self.demande:
                    DemandeVente.objects.filter(pk=self.demande.pk).update(
                        est_payee=True,
                        montant_paye=F('montant_paye') + self.montant,
                        statut='en_traitement'
                    )
                elif self.vente_sticker:
                    VenteSticker.objects.filter(pk=self.vente_sticker.pk).update(
                        est_payee=True,
                        statut='confirmee'
                    )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


# =====================================================
# 5. AVIS CLIENT (dernier car il référence VenteSticker et Demande)
# =====================================================

class AvisClient(models.Model):
    sticker = models.ForeignKey(
        VenteSticker,
        on_delete=models.CASCADE,
        related_name='avis'
    )

    demande = models.ForeignKey(
        'DemandeVente',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='avis'
    )

    client_email = models.EmailField(db_index=True)
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True
    )

    commentaire = models.TextField(blank=True)
    est_valide = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sticker', 'client_email'],
                name='unique_avis_sticker_email'
            ),
            models.UniqueConstraint(
                fields=['demande', 'client_email'],
                condition=Q(demande__isnull=False),
                name='unique_avis_demande_email'
            )
        ]

    def __str__(self):
        return f"Avis {self.note}/5"

Demande = DemandeVente