# apps/ventes/serializers.py
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.utils import timezone
from decimal import Decimal
from .models import (
    VentesSticker, Client, Demande, LigneDemande,
    VentesFacture, Paiement, Panier, ItemPanier,
    AvisClient, CodePromo
)

# ========================================
# SERIALIZERS STICKERS
# ========================================

class VentesStickerSerializer(serializers.ModelSerializer):
    """Serializer complet pour les stickers"""
    prix_ttc = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    dimensions = serializers.CharField(read_only=True)
    surface_cm2 = serializers.FloatField(read_only=True)
    besoin_reapprovisionnement = serializers.BooleanField(read_only=True)
    niveau_stock = serializers.FloatField(read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VentesSticker
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'date_derniere_vente',
            'prix_ttc', 'dimensions', 'surface_cm2',
            'besoin_reapprovisionnement', 'niveau_stock'
        ]
    
    def get_image_url(self, obj):
        if obj.image_principale:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_principale.url)
            return obj.image_principale.url
        return None
    
    def validate_prix_ht(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix HT doit être positif")
        return value
    
    def validate_quantite(self, value):
        if value < 0:
            raise serializers.ValidationError("La quantité ne peut pas être négative")
        return value

class VentesStickerMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les listes de stickers"""
    prix_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VentesSticker
        fields = [
            'id', 'code', 'nom', 'type_sticker',
            'prix_ht', 'prix_ttc', 'image_principale', 'image_url',
            'quantite', 'categorie', 'est_populaire', 'est_nouveau',
            'actif'
        ]
    
    def get_image_url(self, obj):
        if obj.image_principale:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_principale.url)
            return obj.image_principale.url
        return None

class VentesStickerCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de stickers"""
    code = serializers.CharField(
        max_length=50,
        validators=[UniqueValidator(queryset=VentesSticker.objects.all())]
    )
    
    class Meta:
        model = VentesSticker
        fields = [
            'code', 'nom', 'description', 'type_sticker', 'materiau',
            'largeur_mm', 'hauteur_mm', 'forme', 'prix_ht', 'taux_tva',
            'quantite', 'stock_minimum', 'stock_securite',
            'est_personnalisable', 'delai_personnalisation',
            'image_principale', 'categorie', 'tags',
            'poids_g', 'actif', 'est_populaire', 'est_nouveau'
        ]
    
    def create(self, validated_data):
        # Générer automatiquement le code-barres
        validated_data['code_barres'] = f"STK{validated_data['code'].replace('-', '').zfill(10)}"
        return super().create(validated_data)

# ========================================
# SERIALIZERS CLIENTS
# ========================================

class ClientSerializer(serializers.ModelSerializer):
    """Serializer complet pour les clients"""
    nom_complet = serializers.CharField(read_only=True)
    est_fidele = serializers.BooleanField(read_only=True)
    moyenne_panier = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = [
            'code_client', 'created_at', 'updated_at',
            'date_premier_achat', 'date_dernier_achat',
            'montant_total_achats', 'nombre_commandes',
            'points_fidelite', 'nom_complet', 'est_fidele',
            'moyenne_panier'
        ]
    
    def validate_email(self, value):
        """Vérifie que l'email est unique"""
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un client avec cet email existe déjà")
        return value

class ClientMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les listes de clients"""
    nom_complet = serializers.CharField(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'code_client', 'nom_complet', 'email',
            'telephone', 'type_client', 'entreprise',
            'ville', 'est_actif', 'points_fidelite'
        ]

class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de clients"""
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=Client.objects.all())]
    )
    
    class Meta:
        model = Client
        fields = [
            'nom', 'prenom', 'email', 'telephone',
            'type_client', 'adresse', 'ville', 'code_postal', 'pays',
            'entreprise', 'siret', 'tva_intracom',
            'newsletter', 'notes'
        ]
    
    def create(self, validated_data):
        # Générer automatiquement le code client
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        count = Client.objects.filter(
            created_at__date=datetime.now().date()
        ).count() + 1
        validated_data['code_client'] = f"CLI-{date_str}-{count:04d}"
        
        validated_data['est_actif'] = True
        return super().create(validated_data)

# ========================================
# SERIALIZERS LIGNES DE DEMANDE
# ========================================

class LigneDemandeSerializer(serializers.ModelSerializer):
    """Serializer pour les lignes de demande"""
    sticker_details = VentesStickerMinimalSerializer(
        source='sticker', 
        read_only=True
    )
    prix_unitaire_ttc = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    montant_ht = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    montant_tva = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    montant_ttc = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = LigneDemande
        fields = [
            'id', 'demande', 'sticker', 'sticker_details',
            'quantite', 'prix_unitaire_ht', 'prix_unitaire_ttc',
            'taux_tva', 'montant_ht', 'montant_tva', 'montant_ttc',
            'texte_personnalise', 'couleur_personnalisee',
            'fichier_personnalisation'
        ]
        read_only_fields = [
            'prix_unitaire_ht', 'taux_tva',
            'montant_ht', 'montant_tva', 'montant_ttc'
        ]

class LigneDemandeCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une ligne de demande"""
    class Meta:
        model = LigneDemande
        fields = ['sticker', 'quantite', 'texte_personnalise', 'couleur_personnalisee']
    
    def validate(self, data):
        # Vérifier le stock
        sticker = data['sticker']
        quantite = data['quantite']
        
        if sticker.quantite < quantite:
            raise serializers.ValidationError(
                f"Stock insuffisant. Disponible: {sticker.quantite}, Demande: {quantite}"
            )
        
        # Définir automatiquement le prix et la TVA
        data['prix_unitaire_ht'] = sticker.prix_ht
        data['taux_tva'] = sticker.taux_tva
        
        return data

# ========================================
# SERIALIZERS DEMANDES
# ========================================

class DemandeSerializer(serializers.ModelSerializer):
    """Serializer complet pour les demandes"""
    client_details = ClientMinimalSerializer(source='client', read_only=True)
    lignes = LigneDemandeSerializer(many=True, read_only=True)
    montant_restant = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    est_soldee = serializers.BooleanField(read_only=True)
    delai_livraison = serializers.IntegerField(read_only=True)
    created_by_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Demande
        fields = '__all__'
        read_only_fields = [
            'numero', 'created_at', 'updated_at',
            'date_confirmation', 'date_expedition', 'date_livraison',
            'sous_total_ht', 'montant_tva', 'montant_total_ttc',
            'montant_paye', 'montant_restant', 'est_soldee',
            'delai_livraison', 'created_by'
        ]
    
    def get_created_by_details(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'email': obj.created_by.email,
                'username': obj.created_by.username
            }
        return None

class DemandeCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une demande"""
    lignes = LigneDemandeCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Demande
        fields = [
            'client', 'mode_livraison', 'adresse_livraison',
            'mode_paiement', 'notes_client', 'lignes'
        ]
    
    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        request = self.context.get('request')
        
        # Créer la demande
        demande = Demande.objects.create(
            **validated_data,
            created_by=request.user if request and request.user.is_authenticated else None
        )
        
        # Créer les lignes de demande
        for ligne_data in lignes_data:
            LigneDemande.objects.create(demande=demande, **ligne_data)
        
        # Calculer les totaux
        demande.calculer_totaux()
        
        return demande

class DemandeUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour une demande"""
    class Meta:
        model = Demande
        fields = [
            'statut', 'mode_livraison', 'frais_livraison',
            'adresse_livraison', 'transporteur', 'numero_suivi',
            'mode_paiement', 'statut_paiement', 'reference_paiement',
            'date_paiement', 'remise', 'notes_client', 'notes_interne'
        ]
    
    def update(self, instance, validated_data):
        # Si le statut change à "confirmée", appeler la méthode confirmer
        if 'statut' in validated_data and validated_data['statut'] == 'confirmee':
            if instance.statut == 'brouillon':
                instance.confirmer()
                validated_data.pop('statut')  # Ne pas mettre à jour deux fois
        
        return super().update(instance, validated_data)

# ========================================
# SERIALIZERS FACTURES
# ========================================

class VentesFactureSerializer(serializers.ModelSerializer):
    """Serializer pour les factures"""
    demande_details = DemandeSerializer(source='demande', read_only=True)
    client_details = ClientMinimalSerializer(source='client', read_only=True)
    montant_restant = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    est_retard = serializers.BooleanField(read_only=True)
    fichier_pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VentesFacture
        fields = '__all__'
        read_only_fields = [
            'numero', 'created_at', 'updated_at',
            'date_paiement', 'montant_paye', 'montant_restant',
            'est_retard', 'fichier_pdf', 'fichier_xml',
            'created_by'
        ]
    
    def get_fichier_pdf_url(self, obj):
        if obj.fichier_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier_pdf.url)
            return obj.fichier_pdf.url
        return None

# ========================================
# SERIALIZERS PAIEMENTS
# ========================================

class PaiementSerializer(serializers.ModelSerializer):
    """Serializer pour les paiements"""
    facture_details = VentesFactureSerializer(source='facture', read_only=True)
    client_details = ClientMinimalSerializer(source='client', read_only=True)
    
    class Meta:
        model = Paiement
        fields = '__all__'
        read_only_fields = [
            'reference', 'date_enregistrement', 'created_by', 'updated_at'
        ]

class PaiementCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un paiement"""
    class Meta:
        model = Paiement
        fields = [
            'facture', 'client', 'mode', 'montant', 
            'date_paiement', 'numero_cheque', 'banque',
            'reference_virement', 'notes'
        ]
    
    def validate(self, data):
        # Vérifier que le montant est positif
        if data['montant'] <= 0:
            raise serializers.ValidationError("Le montant doit être positif")
        
        # Vérifier la facture si fournie
        if 'facture' in data and data['facture']:
            facture = data['facture']
            if facture.statut == 'payee':
                raise serializers.ValidationError("Cette facture est déjà payée")
        
        return data

# ========================================
# SERIALIZERS PANIER
# ========================================

class ItemPanierSerializer(serializers.ModelSerializer):
    """Serializer pour les items du panier"""
    sticker_details = VentesStickerMinimalSerializer(source='sticker', read_only=True)
    prix_unitaire_ht = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    prix_unitaire_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    montant_ht = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    montant_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemPanier
        fields = [
            'id', 'panier', 'sticker', 'sticker_details',
            'quantite', 'prix_unitaire_ht', 'prix_unitaire_ttc',
            'montant_ht', 'montant_ttc', 'texte_personnalise',
            'couleur_personnalisee', 'date_ajout'
        ]
        read_only_fields = [
            'prix_unitaire_ht', 'prix_unitaire_ttc',
            'montant_ht', 'montant_ttc', 'date_ajout'
        ]

class PanierSerializer(serializers.ModelSerializer):
    """Serializer pour les paniers"""
    items = ItemPanierSerializer(many=True, read_only=True)
    total_ht = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    client_details = ClientMinimalSerializer(source='client', read_only=True)
    
    class Meta:
        model = Panier
        fields = [
            'id', 'client', 'client_details', 'session_key',
            'items', 'total_ht', 'total_ttc',
            'date_creation', 'date_modification', 'est_actif'
        ]
        read_only_fields = [
            'session_key', 'date_creation', 'date_modification'
        ]

# ========================================
# SERIALIZERS AVIS CLIENTS
# ========================================

class AvisClientSerializer(serializers.ModelSerializer):
    """Serializer pour les avis clients"""
    client_details = ClientMinimalSerializer(source='client', read_only=True)
    sticker_details = VentesStickerMinimalSerializer(source='sticker', read_only=True)
    note_etoiles = serializers.CharField(read_only=True)
    pourcentage_utile = serializers.FloatField(read_only=True)
    
    class Meta:
        model = AvisClient
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'utile_oui', 'utile_non',
            'note_etoiles', 'pourcentage_utile'
        ]
    
    def validate_note(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être entre 1 et 5")
        return value

# ========================================
# SERIALIZERS CODES PROMO
# ========================================

class CodePromoSerializer(serializers.ModelSerializer):
    """Serializer pour les codes promo"""
    est_valide = serializers.SerializerMethodField()
    message_validation = serializers.SerializerMethodField()
    
    class Meta:
        model = CodePromo
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'utilisations_actuelles'
        ]
    
    def get_est_valide(self, obj):
        return obj.est_valide()[0]
    
    def get_message_validation(self, obj):
        return obj.est_valide()[1]

# ========================================
# SERIALIZERS STATISTIQUES
# ========================================

class VentesStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de vente"""
    date = serializers.DateField()
    nombre_commandes = serializers.IntegerField()
    chiffre_affaires_ht = serializers.DecimalField(max_digits=12, decimal_places=2)
    chiffre_affaires_ttc = serializers.DecimalField(max_digits=12, decimal_places=2)
    nouveaux_clients = serializers.IntegerField()
    clients_actifs = serializers.IntegerField()
    stickers_vendus = serializers.IntegerField()
    panier_moyen = serializers.DecimalField(max_digits=10, decimal_places=2)

class ClientStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques client"""
    total_clients = serializers.IntegerField()
    clients_actifs = serializers.IntegerField()
    nouveaux_clients_mois = serializers.IntegerField()
    clients_fideles = serializers.IntegerField()
    panier_moyen = serializers.DecimalField(max_digits=10, decimal_places=2)

class StockStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de stock"""
    total_stickers = serializers.IntegerField()
    stickers_actifs = serializers.IntegerField()
    valeur_stock = serializers.DecimalField(max_digits=12, decimal_places=2)
    stickers_en_rupture = serializers.IntegerField()
    stickers_faible_stock = serializers.IntegerField()

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour le dashboard"""
    period = serializers.CharField()
    chiffre_affaires = serializers.DecimalField(max_digits=12, decimal_places=2)
    commandes = serializers.IntegerField()
    nouveaux_clients = serializers.IntegerField()
    stickers_vendus = serializers.IntegerField()
    panier_moyen = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_stickers = serializers.ListField()
    top_clients = serializers.ListField()