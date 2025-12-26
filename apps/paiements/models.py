# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class PaiementsTransaction(models.Model):
    TYPE_CHOICES = (
        ('orange_money', 'Orange Money'),
        ('moov_money', 'Moov Money'),
    )

    reference = models.CharField(unique=True, max_length=100)
    demande = models.OneToOneField('demandes.DemandesDemande', on_delete=models.CASCADE)
    type_paiement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, default='initie')
    donnees_api = models.JSONField(default=dict, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)
    date_validation = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paiements_transaction'

    def __str__(self):
        return f"{self.reference} ({self.statut})"
        verbose_name = 'Transaction de paiement'
        verbose_name_plural = 'Transactions de paiement'
    def __str__(self):
        return f"Transaction {self.reference} - {self.montant} FCFA"
    def get_type_paiement_display(self):
        return dict(self.TYPE_PAIEMENT_CHOICES).get(self.type_paiement, self.type_paiement)
    TYPE_PAIEMENT_CHOICES = (
        ('orange_money', 'Orange Money'),
        ('moove_money', 'Moov Money'),
      )
    STATUT_CHOICES = (
        ('initiee', 'Initiée'),
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('echouee', 'Échouée'),
      )
    def get_statut_display(self):
        return dict(self.STATUT_CHOICES).get(self.statut, self.statut)
    
    @property
    def montant_avec_commission(self):
        return self.montant + self.commission
    @property
    def montant_net(self):
        return self.montant - self.commission
    @property
    def est_reussie(self):
        return self.statut == 'reussie'
    @property
    def est_echouee(self):
        return self.statut == 'echouee'
    @property
    def est_en_attente(self):
        return self.statut == 'en_attente'
    @property
    def est_initiee(self):
        return self.statut == 'initiee'
    def valider_transaction(self):
        self.statut = 'validee'
        from django.utils import timezone
        self.date_validation = timezone.now()
        self.save()
    def echouer_transaction(self):
        self.statut = 'echouee'
        from django.utils import timezone
        self.date_validation = timezone.now()
        self.save()
    