from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import qrcode
import io
from django.core.files.base import ContentFile

User = get_user_model()


class VentesSticker(models.Model):
    """Catalogue des stickers disponibles à la vente."""
    
    class TypeSticker(models.TextChoices):
        DECO = 'deco', _('Décoratif')
        PROMO = 'promo', _('Promotionnel')
        PERSONNALISE = 'personnalise', _('Personnalisé')
        COLLECTIF = 'collectif', _('Collectif')
        LIMITE = 'limite', _('Édition limitée')
        NUMERIQUE = 'numerique', _('Numérique')
    
    class MateriauSticker(models.TextChoices):
        VINYLE = 'vinyle', _('Vinyle')
        PAPIER = 'papier', _('Papier brillant')
        MAT = 'mat', _('Vinyle mat')
        TRANSPARENT = 'transparent', _('Transparent')
        REFLECHISSANT = 'reflechissant', _('Réfléchissant')
    
    # Identifiants
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Code produit"),
        help_text=_("Code unique du sticker")
    )
    
    # Caractéristiques
    nom = models.CharField(
        max_length=200,
        verbose_name=_("Nom du sticker")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    type_sticker = models.CharField(
        max_length=50,
        choices=TypeSticker.choices,
        verbose_name=_("Type de sticker")
    )
    materiau = models.CharField(
        max_length=50,
        choices=MateriauSticker.choices,
        default=MateriauSticker.VINYLE,
        verbose_name=_("Matériau")
    )
    
    # Dimensions
    largeur_mm = models.IntegerField(
        verbose_name=_("Largeur (mm)"),
        help_text=_("Largeur en millimètres")
    )
    hauteur_mm = models.IntegerField(
        verbose_name=_("Hauteur (mm)"),
        help_text=_("Hauteur en millimètres")
    )
    forme = models.CharField(
        max_length=20,
        choices=[
            ('rectangle', _('Rectangle')),
            ('carre', _('Carré')),
            ('rond', _('Rond')),
            ('ovale', _('Ovale')),
            ('personnalise', _('Personnalisé')),
        ],
        default='rectangle',
        verbose_name=_("Forme")
    )
    
    # Prix
    prix_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Prix HT")
    )
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Taux TVA (%)")
    )
    
    @property
    def prix_ttc(self):
        """Calcule le prix TTC."""
        return self.prix_ht * (1 + self.taux_tva / 100)
    
    # Stock
    quantite = models.IntegerField(
        verbose_name=_("Stock disponible"),
        help_text=_("Quantité en stock")
    )
    stock_minimum = models.IntegerField(
        default=10,
        verbose_name=_("Stock minimum"),
        help_text=_("Seuil pour alerte réapprovisionnement")
    )
    stock_securite = models.IntegerField(
        default=5,
        verbose_name=_("Stock de sécurité"),
        help_text=_("Stock réservé pour les urgences")
    )
    
    # Personnalisation
    est_personnalisable = models.BooleanField(
        default=False,
        verbose_name=_("Personnalisable")
    )
    delai_personnalisation = models.IntegerField(
        default=3,
        verbose_name=_("Délai personnalisation (jours)")
    )
    
    # Images
    image_principale = models.ImageField(
        upload_to='stickers/',
        null=True,
        blank=True,
        verbose_name=_("Image principale")
    )
    images_supplementaires = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Images supplémentaires")
    )
    
    # Catégorisation
    categorie = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Catégorie")
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags")
    )
    
    # Métadonnées
    code_barres = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Code-barres")
    )
    poids_g = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5,
        verbose_name=_("Poids (g)")
    )
    
    # Statut
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    est_populaire = models.BooleanField(
        default=False,
        verbose_name=_("Populaire")
    )
    est_nouveau = models.BooleanField(
        default=True,
        verbose_name=_("Nouveau")
    )
    
    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    date_derniere_vente = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière vente")
    )
    
    class Meta:
        # managed = True  # Changez à True pour que Django gère la table
        db_table = 'ventes_sticker'
        verbose_name = _("Sticker")
        verbose_name_plural = _("Stickers")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type_sticker']),
            models.Index(fields=['actif']),
            models.Index(fields=['categorie']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le code-barres si vide."""
        if not self.code_barres and self.code:
            self.code_barres = f"STK{self.code.replace('-', '').zfill(10)}"
        super().save(*args, **kwargs)
    
    @property
    def dimensions(self):
        """Retourne les dimensions formatées."""
        return f"{self.largeur_mm}×{self.hauteur_mm} mm"
    
    @property
    def surface_cm2(self):
        """Calcule la surface en cm²."""
        return (self.largeur_mm * self.hauteur_mm) / 100
    
    @property
    def besoin_reapprovisionnement(self):
        """Détermine si besoin de réapprovisionnement."""
        return self.quantite <= self.stock_minimum
    
    @property
    def niveau_stock(self):
        """Retourne le niveau de stock en pourcentage."""
        if self.stock_securite > 0:
            return (self.quantite / self.stock_securite) * 100
        return 0


class Client(models.Model):
    """Clients pour la vente de stickers."""
    
    class TypeClient(models.TextChoices):
        PARTICULIER = 'particulier', _('Particulier')
        PROFESSIONNEL = 'professionnel', _('Professionnel')
        REVENDEUR = 'revendeur', _('Revendeur')
        ADMINISTRATION = 'administration', _('Administration')
    
    # Identifiants
    code_client = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code client")
    )
    email = models.EmailField(
        unique=True,
        verbose_name=_("Email")
    )
    
    # Informations personnelles
    prenom = models.CharField(
        max_length=100,
        verbose_name=_("Prénom")
    )
    nom = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Téléphone")
    )
    
    # Type de client
    type_client = models.CharField(
        max_length=20,
        choices=TypeClient.choices,
        default=TypeClient.PARTICULIER,
        verbose_name=_("Type de client")
    )
    
    # Adresse
    adresse = models.TextField(
        blank=True,
        verbose_name=_("Adresse")
    )
    ville = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Ville")
    )
    code_postal = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Code postal")
    )
    pays = models.CharField(
        max_length=100,
        default='France',
        verbose_name=_("Pays")
    )
    
    # Informations professionnelles (si applicable)
    entreprise = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Entreprise")
    )
    siret = models.CharField(
        max_length=14,
        blank=True,
        verbose_name=_("SIRET")
    )
    tva_intracom = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("TVA intracommunautaire")
    )
    
    # Préférences et statut
    newsletter = models.BooleanField(
        default=True,
        verbose_name=_("Inscrit à la newsletter")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    points_fidelite = models.IntegerField(
        default=0,
        verbose_name=_("Points fidélité")
    )
    
    # Statistiques
    date_premier_achat = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Premier achat")
    )
    date_dernier_achat = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernier achat")
    )
    montant_total_achats = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total achats")
    )
    nombre_commandes = models.IntegerField(
        default=0,
        verbose_name=_("Nombre de commandes")
    )
    
    # Métadonnées
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    
    class Meta:
        db_table = 'ventes_client'
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ['nom', 'prenom']
        indexes = [
            models.Index(fields=['code_client']),
            models.Index(fields=['email']),
            models.Index(fields=['type_client']),
        ]
    
    def __str__(self):
        if self.type_client == self.TypeClient.PARTICULIER:
            return f"{self.prenom} {self.nom}"
        return f"{self.entreprise or self.nom} ({self.code_client})"
    
    @property
    def nom_complet(self):
        if self.type_client == self.TypeClient.PARTICULIER:
            return f"{self.prenom} {self.nom}".strip()
        return self.entreprise or self.nom
    
    @property
    def est_fidele(self):
        """Détermine si le client est fidèle."""
        return self.points_fidelite >= 100 or self.nombre_commandes >= 5
    
    @property
    def moyenne_panier(self):
        """Calcule le panier moyen."""
        if self.nombre_commandes > 0:
            return self.montant_total_achats / self.nombre_commandes
        return Decimal('0')
    
    def ajouter_points_fidelite(self, points):
        """Ajoute des points de fidélité."""
        self.points_fidelite += points
        self.save()
    
    def mettre_a_jour_statistiques(self, montant_commande):
        """Met à jour les statistiques après une commande."""
        self.nombre_commandes += 1
        self.montant_total_achats += montant_commande
        
        if not self.date_premier_achat:
            self.date_premier_achat = timezone.now()
        
        self.date_dernier_achat = timezone.now()
        
        # Ajouter des points de fidélité (1 point par euro)
        points = int(montant_commande)
        self.ajouter_points_fidelite(points)
        
        self.save()


class Demande(models.Model):
    """Demandes/commandes de stickers."""
    
    class StatutDemande(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        EN_ATTENTE = 'en_attente', _('En attente')
        CONFIRMEE = 'confirmee', _('Confirmée')
        EN_PREPARATION = 'preparation', _('En préparation')
        EXPEDIEE = 'expediee', _('Expédiée')
        LIVREE = 'livree', _('Livrée')
        ANNULEE = 'annulee', _('Annulée')
    
    class ModeLivraison(models.TextChoices):
        STANDARD = 'standard', _('Standard')
        EXPRESS = 'express', _('Express')
        POINT_RELAIS = 'relais', _('Point relais')
        RETRAIT = 'retrait', _('Retrait sur place')
    
    class ModePaiement(models.TextChoices):
        CARTE = 'carte', _('Carte bancaire')
        VIREMENT = 'virement', _('Virement')
        CHEQUE = 'cheque', _('Chèque')
        ESPECES = 'especes', _('Espèces')
    
    # Identifiants
    numero = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de demande")
    )
    
    # Client
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='demandes',
        verbose_name=_("Client")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=StatutDemande.choices,
        default=StatutDemande.BROUILLON,
        verbose_name=_("Statut")
    )
    
    # Dates importantes
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_confirmation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de confirmation")
    )
    date_expedition = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'expédition")
    )
    date_livraison = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de livraison")
    )
    
    # Livraison
    mode_livraison = models.CharField(
        max_length=20,
        choices=ModeLivraison.choices,
        default=ModeLivraison.STANDARD,
        verbose_name=_("Mode de livraison")
    )
    frais_livraison = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Frais de livraison")
    )
    adresse_livraison = models.TextField(
        blank=True,
        verbose_name=_("Adresse de livraison")
    )
    transporteur = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Transporteur")
    )
    numero_suivi = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Numéro de suivi")
    )
    
    # Paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=ModePaiement.choices,
        blank=True,
        verbose_name=_("Mode de paiement")
    )
    statut_paiement = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', _('En attente')),
            ('partiel', _('Partiel')),
            ('paye', _('Payé')),
            ('retard', _('En retard')),
            ('annule', _('Annulé')),
        ],
        default='en_attente',
        verbose_name=_("Statut paiement")
    )
    reference_paiement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence paiement")
    )
    date_paiement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Calculs financiers
    sous_total_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Sous-total HT")
    )
    remise = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Remise")
    )
    montant_tva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant TVA")
    )
    montant_total_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total TTC")
    )
    montant_paye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant payé")
    )
    
    # Métadonnées
    notes_client = models.TextField(
        blank=True,
        verbose_name=_("Notes client")
    )
    notes_interne = models.TextField(
        blank=True,
        verbose_name=_("Notes interne")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='demandes_crees',
        verbose_name=_("Créé par")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    
    class Meta:
        db_table = 'demandes_demande'
        verbose_name = _("Demande")
        verbose_name_plural = _("Demandes")
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['client']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['statut_paiement']),
        ]
    
    def __str__(self):
        return f"Demande {self.numero} - {self.client.nom_complet}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le numéro de demande."""
        if not self.numero:
            annee = timezone.now().year
            mois = timezone.now().month
            count = Demande.objects.filter(
                date_creation__year=annee,
                date_creation__month=mois
            ).count() + 1
            self.numero = f"DEM-{annee}{mois:02d}-{count:04d}"
        
        super().save(*args, **kwargs)
    
    def calculer_totaux(self):
        """Calcule les totaux de la demande."""
        lignes = self.lignes.all()
        
        # Sous-total HT
        sous_total = Decimal('0')
        montant_tva = Decimal('0')
        
        for ligne in lignes:
            sous_total += ligne.montant_ht
            montant_tva += ligne.montant_tva
        
        # Total TTC
        total_ttc = sous_total - self.remise + montant_tva + self.frais_livraison
        
        self.sous_total_ht = sous_total
        self.montant_tva = montant_tva
        self.montant_total_ttc = total_ttc
        
        self.save()
    
    def confirmer(self):
        """Confirme la demande."""
        if self.statut != self.StatutDemande.BROUILLON:
            raise ValueError("Seules les demandes brouillon peuvent être confirmées")
        
        self.statut = self.StatutDemande.CONFIRMEE
        self.date_confirmation = timezone.now()
        
        # Mettre à jour le stock des stickers
        for ligne in self.lignes.all():
            ligne.sticker.quantite -= ligne.quantite
            ligne.sticker.date_derniere_vente = timezone.now()
            ligne.sticker.save()
        
        # Mettre à jour les statistiques du client
        self.client.mettre_a_jour_statistiques(self.montant_total_ttc)
        
        self.save()
    
    def expedier(self, transporteur, numero_suivi):
        """Marque la demande comme expédiée."""
        self.statut = self.StatutDemande.EXPEDIEE
        self.date_expedition = timezone.now()
        self.transporteur = transporteur
        self.numero_suivi = numero_suivi
        self.save()
    
    @property
    def montant_restant(self):
        """Calcule le montant restant à payer."""
        return self.montant_total_ttc - self.montant_paye
    
    @property
    def est_soldee(self):
        """Vérifie si la demande est soldée."""
        return self.montant_restant <= Decimal('0.01')
    
    @property
    def delai_livraison(self):
        """Estime le délai de livraison."""
        if self.date_expedition and self.date_livraison:
            return (self.date_livraison - self.date_expedition).days
        
        # Estimation basée sur le mode de livraison
        delais = {
            'standard': 5,
            'express': 2,
            'relais': 4,
            'retrait': 0,
        }
        return delais.get(self.mode_livraison, 5)


class LigneDemande(models.Model):
    """Lignes de demande (produits commandés)."""
    
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name=_("Demande")
    )
    sticker = models.ForeignKey(
        VentesSticker,
        on_delete=models.PROTECT,
        related_name='lignes_demande',
        verbose_name=_("Sticker")
    )
    quantite = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Quantité")
    )
    prix_unitaire_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Prix unitaire HT")
    )
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.0,
        verbose_name=_("Taux TVA (%)")
    )
    
    # Personnalisation
    texte_personnalise = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Texte personnalisé")
    )
    couleur_personnalisee = models.CharField(
        max_length=7,
        blank=True,
        verbose_name=_("Couleur personnalisée")
    )
    fichier_personnalisation = models.FileField(
        upload_to='personnalisations/',
        null=True,
        blank=True,
        verbose_name=_("Fichier de personnalisation")
    )
    
    # Calculés
    @property
    def prix_unitaire_ttc(self):
        return self.prix_unitaire_ht * (1 + self.taux_tva / 100)
    
    @property
    def montant_ht(self):
        return self.prix_unitaire_ht * self.quantite
    
    @property
    def montant_tva(self):
        return self.montant_ht * (self.taux_tva / 100)
    
    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva
    
    class Meta:
        db_table = 'ventes_ligne_demande'
        verbose_name = _("Ligne de demande")
        verbose_name_plural = _("Lignes de demande")
        unique_together = ['demande', 'sticker']
    
    def __str__(self):
        return f"{self.sticker.nom} x{self.quantite}"


class VentesFacture(models.Model):
    """Factures émises pour les demandes."""
    
    class StatutFacture(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        EMISE = 'emise', _('Emise')
        ENVOYEE = 'envoyee', _('Envoyée')
        PAYEE = 'payee', _('Payée')
        ANNULEE = 'annulee', _('Annulée')
    
    # Identifiants
    numero = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de facture")
    )
    
    # Références
    demande = models.ForeignKey(
        Demande,
        on_delete=models.PROTECT,
        related_name='factures',
        verbose_name=_("Demande")
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='factures',
        verbose_name=_("Client")
    )
    
    # Dates
    date_emission = models.DateField(
        default=timezone.now,
        verbose_name=_("Date d'émission")
    )
    date_echeance = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'échéance")
    )
    date_paiement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=StatutFacture.choices,
        default=StatutFacture.BROUILLON,
        verbose_name=_("Statut")
    )
    
    # Montants
    montant_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant HT")
    )
    tva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant TVA")
    )
    montant_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant TTC")
    )
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant payé")
    )
    
    # Fichiers
    fichier_pdf = models.FileField(
        upload_to='factures/pdf/',
        null=True,
        blank=True,
        verbose_name=_("Fichier PDF")
    )
    fichier_xml = models.FileField(
        upload_to='factures/xml/',
        null=True,
        blank=True,
        verbose_name=_("Fichier XML")
    )
    
    # Métadonnées
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='factures_crees',
        verbose_name=_("Créé par")
    )
    
    class Meta:
        # managed = True  # Changez à True pour que Django gère la table
        db_table = 'ventes_facture'
        verbose_name = _("Facture")
        verbose_name_plural = _("Factures")
        ordering = ['-date_emission']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['demande']),
            models.Index(fields=['client']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_emission']),
        ]
    
    def __str__(self):
        return f"Facture {self.numero} - {self.client.nom_complet}"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le numéro de facture."""
        if not self.numero:
            annee = timezone.now().year
            count = VentesFacture.objects.filter(
                date_emission__year=annee
            ).count() + 1
            self.numero = f"FAC-{annee}-{count:05d}"
        
        # Calculer la date d'échéance si non définie
        if not self.date_echeance:
            self.date_echeance = self.date_emission + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def emettre(self):
        """Émet la facture."""
        if self.statut != self.StatutFacture.BROUILLON:
            raise ValueError("Seules les factures brouillon peuvent être émises")
        
        self.statut = self.StatutFacture.EMISE
        self.save()
    
    def enregistrer_paiement(self, montant, date_paiement=None):
        """Enregistre un paiement sur la facture."""
        self.montant_paye += montant
        
        if self.montant_paye >= self.montant_ttc:
            self.statut = self.StatutFacture.PAYEE
            self.date_paiement = date_paiement or timezone.now().date()
        elif self.montant_paye > 0:
            self.statut = self.StatutFacture.ENVOYEE
        
        self.save()
    
    @property
    def montant_restant(self):
        """Calcule le montant restant à payer."""
        return self.montant_ttc - self.montant_paye
    
    @property
    def est_retard(self):
        """Vérifie si la facture est en retard."""
        if self.date_echeance and self.statut != self.StatutFacture.PAYEE:
            return timezone.now().date() > self.date_echeance
        return False


class Paiement(models.Model):
    """Paiements des clients."""
    
    class ModePaiement(models.TextChoices):
        CARTE = 'carte', _('Carte bancaire')
        VIREMENT = 'virement', _('Virement')
        CHEQUE = 'cheque', _('Chèque')
        ESPECES = 'especes', _('Espèces')
        PREPAYEMENT = 'prepaiement', _('Prépaiement')
    
    # Identifiants
    reference = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Référence paiement")
    )
    
    # Références
    facture = models.ForeignKey(
        VentesFacture,
        on_delete=models.PROTECT,
        related_name='paiements',
        null=True,
        blank=True,
        verbose_name=_("Facture")
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name=_("Client")
    )
    
    # Informations paiement
    mode = models.CharField(
        max_length=20,
        choices=ModePaiement.choices,
        verbose_name=_("Mode de paiement")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant")
    )
    date_paiement = models.DateField(
        default=timezone.now,
        verbose_name=_("Date de paiement")
    )
    date_enregistrement = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'enregistrement")
    )
    
    # Détails spécifiques
    numero_cheque = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Numéro de chèque")
    )
    banque = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Banque")
    )
    reference_virement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence virement")
    )
    
    # Statut
    est_valide = models.BooleanField(
        default=True,
        verbose_name=_("Valide")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='paiements_crees',
        verbose_name=_("Enregistré par")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    
    class Meta:
        db_table = 'ventes_paiement'
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['facture']),
            models.Index(fields=['client']),
            models.Index(fields=['mode']),
        ]
    
    def __str__(self):
        return f"Paiement {self.reference} - {self.montant}€"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement la référence."""
        if not self.reference:
            date_str = self.date_paiement.strftime('%Y%m%d')
            count = Paiement.objects.filter(
                date_paiement=self.date_paiement
            ).count() + 1
            self.reference = f"PAY-{date_str}-{count:04d}"
        
        super().save(*args, **kwargs)
        
        # Mettre à jour le statut de la facture
        if self.facture:
            self.facture.enregistrer_paiement(self.montant, self.date_paiement)


class Panier(models.Model):
    """Panier d'achat temporaire."""
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='paniers',
        verbose_name=_("Client")
    )
    session_key = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Clé de session")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    
    class Meta:
        db_table = 'ventes_panier'
        verbose_name = _("Panier")
        verbose_name_plural = _("Paniers")
        ordering = ['-date_modification']
    
    def __str__(self):
        return f"Panier de {self.client.nom_complet}"
    
    @property
    def total_ht(self):
        total = Decimal('0')
        for item in self.items.all():
            total += item.montant_ht
        return total
    
    @property
    def total_ttc(self):
        total = Decimal('0')
        for item in self.items.all():
            total += item.montant_ttc
        return total
    
    def vider(self):
        """Vide le panier."""
        self.items.all().delete()


class ItemPanier(models.Model):
    """Items dans le panier."""
    
    panier = models.ForeignKey(
        Panier,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Panier")
    )
    sticker = models.ForeignKey(
        VentesSticker,
        on_delete=models.CASCADE,
        related_name='items_panier',
        verbose_name=_("Sticker")
    )
    quantite = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Quantité")
    )
    
    # Personnalisation
    texte_personnalise = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Texte personnalisé")
    )
    couleur_personnalisee = models.CharField(
        max_length=7,
        blank=True,
        verbose_name=_("Couleur personnalisée")
    )
    
    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'ajout")
    )
    
    class Meta:
        db_table = 'ventes_item_panier'
        verbose_name = _("Item du panier")
        verbose_name_plural = _("Items du panier")
        unique_together = ['panier', 'sticker']
    
    def __str__(self):
        return f"{self.sticker.nom} x{self.quantite}"
    
    @property
    def prix_unitaire_ht(self):
        return self.sticker.prix_ht
    
    @property
    def prix_unitaire_ttc(self):
        return self.sticker.prix_ttc
    
    @property
    def montant_ht(self):
        return self.prix_unitaire_ht * self.quantite
    
    @property
    def montant_ttc(self):
        return self.prix_unitaire_ttc * self.quantite


class AvisClient(models.Model):
    """Avis des clients sur les stickers."""
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name=_("Client")
    )
    sticker = models.ForeignKey(
        VentesSticker,
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name=_("Sticker")
    )
    commande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name=_("Commande")
    )
    
    # Évaluation
    note = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note (1-5)")
    )
    titre = models.CharField(
        max_length=200,
        verbose_name=_("Titre")
    )
    commentaire = models.TextField(
        verbose_name=_("Commentaire")
    )
    
    # Photos
    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Photos")
    )
    
    # Validation
    est_valide = models.BooleanField(
        default=False,
        verbose_name=_("Validé")
    )
    est_modere = models.BooleanField(
        default=False,
        verbose_name=_("Modéré")
    )
    
    # Utilité
    utile_oui = models.IntegerField(
        default=0,
        verbose_name=_("Utile : Oui")
    )
    utile_non = models.IntegerField(
        default=0,
        verbose_name=_("Utile : Non")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    
    class Meta:
        db_table = 'ventes_avis_client'
        verbose_name = _("Avis client")
        verbose_name_plural = _("Avis clients")
        ordering = ['-created_at']
        unique_together = ['client', 'sticker']
    
    def __str__(self):
        return f"Avis de {self.client.nom_complet} sur {self.sticker.nom}"
    
    @property
    def note_etoiles(self):
        """Retourne la note en étoiles."""
        return '★' * self.note + '☆' * (5 - self.note)
    
    @property
    def pourcentage_utile(self):
        total = self.utile_oui + self.utile_non
        if total > 0:
            return (self.utile_oui / total) * 100
        return 0


class CodePromo(models.Model):
    """Codes promotionnels."""
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Code")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    # Type de réduction
    type_reduction = models.CharField(
        max_length=20,
        choices=[
            ('pourcentage', _('Pourcentage')),
            ('montant_fixe', _('Montant fixe')),
            ('livraison_gratuite', _('Livraison gratuite')),
        ],
        default='pourcentage',
        verbose_name=_("Type de réduction")
    )
    valeur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Valeur")
    )
    montant_minimum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant minimum")
    )
    
    # Validité
    date_debut = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Date début")
    )
    date_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date fin")
    )
    utilisations_max = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Utilisations maximum")
    )
    utilisations_actuelles = models.IntegerField(
        default=0,
        verbose_name=_("Utilisations actuelles")
    )
    
    # Restrictions
    clients_cibles = models.ManyToManyField(
        Client,
        blank=True,
        related_name='codes_promo',
        verbose_name=_("Clients cibles")
    )
    stickers_cibles = models.ManyToManyField(
        VentesSticker,
        blank=True,
        related_name='codes_promo',
        verbose_name=_("Stickers cibles")
    )
    
    # Statut
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )
    
    class Meta:
        db_table = 'ventes_code_promo'
        verbose_name = _("Code promotionnel")
        verbose_name_plural = _("Codes promotionnels")
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.code
    
    def est_valide(self, client=None, montant_panier=0):
        """Vérifie si le code promo est valide."""
        now = timezone.now()
        
        # Vérifications de base
        if not self.est_actif:
            return False, "Code promo inactif"
        
        if now < self.date_debut:
            return False, "Code promo pas encore valide"
        
        if self.date_fin and now > self.date_fin:
            return False, "Code promo expiré"
        
        if self.utilisations_max and self.utilisations_actuelles >= self.utilisations_max:
            return False, "Limite d'utilisations atteinte"
        
        # Vérification du montant minimum
        if montant_panier < self.montant_minimum:
            return False, f"Montant minimum requis: {self.montant_minimum}€"
        
        # Vérification du client cible
        if client and self.clients_cibles.exists():
            if not self.clients_cibles.filter(id=client.id).exists():
                return False, "Code promo non valide pour ce client"
        
        return True, "Code promo valide"
    
    def appliquer_reduction(self, montant):
        """Applique la réduction au montant."""
        if self.type_reduction == 'pourcentage':
            reduction = montant * (self.valeur / 100)
        elif self.type_reduction == 'montant_fixe':
            reduction = self.valeur
        elif self.type_reduction == 'livraison_gratuite':
            reduction = 0  # Géré séparément
        else:
            reduction = 0
        
        return max(reduction, 0)
    
    def utiliser(self):
        """Enregistre une utilisation du code."""
        self.utilisations_actuelles += 1
        self.save()