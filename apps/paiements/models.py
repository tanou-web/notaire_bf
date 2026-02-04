from django.db import models
from django.utils import timezone

class PaiementsTransaction(models.Model):
    TYPE_CHOICES = (
        ('yengapay', 'Yengapay (Orange, Moov, Sank, Telecel)'),
    )

    STATUT_CHOICES = (
        ('initiee', 'Initiée'),
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('echouee', 'Échouée'),
    )

    reference = models.CharField(unique=True, max_length=100)
    demande = models.OneToOneField('demandes.DemandesDemande', on_delete=models.CASCADE)
    type_paiement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='initiee')
    donnees_api = models.JSONField(default=dict, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)
    date_validation = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'paiements_transaction'
        verbose_name = 'Transaction de paiement'
        verbose_name_plural = 'Transactions de paiement'

    def __str__(self):
        return f"Transaction {self.reference} - {self.montant} FCFA"

    @property
    def montant_avec_commission(self):
        return self.montant + self.commission

    @property
    def montant_net(self):
        return self.montant - self.commission

    @property
    def est_reussie(self):
        return self.statut == 'validee'

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
        self.date_validation = timezone.now()
        self.save()

    def echouer_transaction(self):
        self.statut = 'echouee'
        self.date_validation = timezone.now()
        self.save()
