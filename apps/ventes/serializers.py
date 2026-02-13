# apps/ventes/serializers.py
from rest_framework import serializers
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from datetime import timedelta
import re
import uuid

from .models import VenteSticker, Demande, Paiement, AvisClient, CodePromo, ReferenceSticker, VenteStickerNotaire



# ========================================
# 1. SERIALIZERS STICKERS
# ========================================

class VentesStickerSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des stickers
    """
    prix_ttc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    en_stock = serializers.BooleanField(source='disponible', read_only=True)
    sticker_nom = serializers.CharField(source='sticker.nom', read_only=True)

    class Meta:
        model = VenteSticker
        fields = [
            'id',
            'reference',
            'sticker',
            'sticker_nom',   # ✅ OK
            'client_email',
            'prix_ttc', 
            'en_stock',
            'quantite',
            'prix_unitaire',
            'montant_total',
            'statut',
            'est_payee',
            'date_vente',
        ]

class VenteStickerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'une vente de sticker
    """
    class Meta:
        model = VenteSticker
        fields = [
            'sticker', 'quantite', 
            'client_nom', 'client_email', 'client_contact',
            'notaire'
        ]
    
    def validate(self, data):
        # Normaliser l'email
        if 'client_email' in data and data['client_email']:
            data['client_email'] = data['client_email'].lower().strip()
        
        # Normaliser le contact téléphonique
        if 'client_contact' in data and data['client_contact']:
            # Garder uniquement les chiffres
            data['client_contact'] = ''.join(
                c for c in str(data['client_contact']) if c.isdigit()
            )
            
            # Validation format Burkinabè
            phone = data['client_contact']
            if len(phone) == 9 and phone.startswith('0'):
                # Format 0XXXXXXXX → +226XXXXXXXX
                data['client_contact'] = '+226' + phone[1:]
            elif len(phone) == 8:
                # Format XXXXXXXX → +226XXXXXXXX
                data['client_contact'] = '+226' + phone
        
        # Validation de la quantité
        if 'quantite' in data and data['quantite'] <= 0:
            raise serializers.ValidationError({
                'quantite': 'La quantité doit être supérieure à 0'
            })
        
        return data
    
    def validate_quantite(self, value):
        """
        Validation spécifique de la quantité
        """
        if value < 1:
            raise serializers.ValidationError("La quantité minimale est 1")
        if value > 100:
            raise serializers.ValidationError("La quantité maximale est 100")
        return value
    
    def validate_client_email(self, value):
        """
        Validation de l'email
        """
        if value:
            validator = EmailValidator()
            try:
                validator(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Adresse email invalide")
        return value


# ========================================
# 2. SERIALIZERS DEMANDES
# ========================================

class DemandeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'une demande SANS COMPTE
    """
    code_promo = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Demande
        fields = [
            'document', 'client_nom', 'client_email', 
            'client_contact', 'description', 'code_promo'
        ]
    
    def validate(self, data):
        # Normaliser l'email
        if 'client_email' in data and data['client_email']:
            data['client_email'] = data['client_email'].lower().strip()
        
        # Normaliser le contact téléphonique
        if 'client_contact' in data and data['client_contact']:
            phone = ''.join(c for c in str(data['client_contact']) if c.isdigit())
            data['client_contact'] = self._normaliser_telephone(phone)
        
        return data
    
    def _normaliser_telephone(self, phone):
        """
        Normaliser le numéro de téléphone au format international
        """
        if not phone:
            return phone
        
        if len(phone) == 9 and phone.startswith('0'):
            # Format 0XXXXXXXX → +226XXXXXXXX
            return '+226' + phone[1:]
        elif len(phone) == 8:
            # Format XXXXXXXX → +226XXXXXXXX
            return '+226' + phone
        elif phone.startswith('226') and len(phone) == 11:
            # Format 226XXXXXXXX → +226XXXXXXXX
            return '+' + phone
        elif phone.startswith('00226') and len(phone) == 14:
            # Format 00226XXXXXXXX → +226XXXXXXXX
            return '+226' + phone[5:]
        
        # Si déjà format +226...
        if phone.startswith('+226') and len(phone) == 12:
            return phone
        
        # Autres formats non reconnus
        return phone
    
    def validate_client_email(self, value):
        """
        Validation de l'email
        """
        if value:
            validator = EmailValidator()
            try:
                validator(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Adresse email invalide")
        return value
    
    def validate_client_contact(self, value):
        """
        Validation du numéro de téléphone Burkinabè
        """
        if value:
            # Nettoyer le numéro
            phone = ''.join(c for c in str(value) if c.isdigit())
            
            # Vérifier si c'est un format Burkinabè valide
            patterns = [
                r'^226[0-9]{8}$',      # 226XXXXXXXX
                r'^0[0-9]{8}$',        # 0XXXXXXXX
                r'^\+226[0-9]{8}$',    # +226XXXXXXXX
                r'^00226[0-9]{8}$',    # 00226XXXXXXXX
            ]
            
            valid = any(re.match(pattern, phone) for pattern in patterns)
            if not valid:
                raise serializers.ValidationError(
                    "Numéro de téléphone invalide. Format attendu: 0XXXXXXXX ou +226XXXXXXXX"
                )
        
        return value
    
    def create(self, validated_data):
        """
        Création avec génération automatique des champs
        """
        # Extraire le code promo si présent
        code_promo = validated_data.pop('code_promo', None)
        
        # Calculer le montant
        document = validated_data.get('document')
        montant_base = document.prix_ttc if document else 0
        
        # Appliquer réduction si code promo valide
        montant_final = montant_base
        reduction_appliquee = 0
        
        if code_promo:
            from .services import CodePromoService
            try:
                promo = CodePromoService.valider_code_promo(
                    code=code_promo,
                    type_utilisateur='client_externe'
                )
                if promo:
                    reduction_appliquee = (montant_base * promo.pourcentage_reduction) / 100
                    montant_final = montant_base - reduction_appliquee
                    validated_data['code_promo_applique'] = promo
            except DjangoValidationError:
                pass  # Code invalide, on ignore
        
        # Ajouter les champs calculés
        validated_data['montant_total'] = montant_final
        validated_data['montant_base'] = montant_base
        validated_data['reduction_appliquee'] = reduction_appliquee
        
        # Générer les tokens et références
        validated_data['reference'] = f"DEM-{uuid.uuid4().hex[:8].upper()}"
        validated_data['token_acces'] = uuid.uuid4()
        validated_data['token_expire'] = timezone.now() + timedelta(days=7)
        
        # Ajouter informations de suivi
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self._get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Générer le lien de suivi
        validated_data['lien_suivi'] = (
            f"{self.context.get('frontend_url', '')}/suivi/"
            f"{validated_data['token_acces']}"
        )
        
        return super().create(validated_data)
    
    def _get_client_ip(self, request):
        """
        Récupérer l'adresse IP du client
        """
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class DemandeSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des demandes
    """
    nom_complet_client = serializers.CharField(read_only=True)
    token_valide = serializers.BooleanField(read_only=True)
    est_payee = serializers.BooleanField(read_only=True)
    lien_suivi = serializers.CharField(read_only=True)
    document_nom = serializers.CharField(source='document.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Demande
        fields = [
            'id', 'reference', 'nom_complet_client', 
            'document', 'document_nom',
            'client_email', 'client_contact',
            'statut', 'statut_display',
            'montant_total', 'montant_base', 'reduction_appliquee',
            'est_payee', 'token_acces', 'token_valide', 'lien_suivi',
            'notaire_nom_complet', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


# ========================================
# 3. SERIALIZERS PAIEMENTS
# ========================================

class PaiementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les paiements
    """
    type_transaction = serializers.CharField(read_only=True)
    reference_transaction = serializers.CharField(read_only=True)
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'reference', 'montant', 'type_paiement',
            'type_transaction', 'reference_transaction',
            'statut', 'date_creation', 'date_validation'
        ]
        read_only_fields = fields
    
    def get_type_transaction(self, obj):
        """
        Déterminer le type de transaction (demande ou vente_sticker)
        """
        if obj.demande:
            return 'demande'
        elif obj.vente_sticker:
            return 'vente_sticker'
        return 'inconnu'
    
    def get_reference_transaction(self, obj):
        """
        Récupérer la référence de la transaction liée
        """
        if obj.demande:
            return obj.demande.reference
        elif obj.vente_sticker:
            return obj.vente_sticker.reference
        return ''


class PaiementInitierSerializer(serializers.Serializer):
    """
    Serializer pour initier un paiement
    """
    type_transaction = serializers.ChoiceField(
        choices=['demande', 'vente_sticker']
    )
    reference = serializers.CharField(max_length=50)
    type_paiement = serializers.ChoiceField(
        choices=['orange_money', 'mtn_money', 'carte_bancaire', 'especes'],
        default='orange_money'
    )
    
    def validate(self, data):
        # Vérifier que la transaction existe
        type_transaction = data['type_transaction']
        reference = data['reference']
        
        try:
            if type_transaction == 'demande':
                Demande.objects.get(reference=reference)
            elif type_transaction == 'vente_sticker':
                VenteSticker.objects.get(reference=reference)
        except (Demande.DoesNotExist, VenteSticker.DoesNotExist):
            raise serializers.ValidationError({
                'reference': f"Transaction {reference} introuvable"
            })
        
        return data


# ========================================
# 4. SERIALIZERS AVIS CLIENTS
# ========================================

class AvisClientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'avis SANS COMPTE
    """
    class Meta:
        model = AvisClient
        fields = [
            'sticker', 'client_nom', 'client_email',
            'note', 'titre', 'commentaire'
        ]
    
    def validate_client_email(self, value):
        """
        Validation de l'email
        """
        if value:
            validator = EmailValidator()
            try:
                validator(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Adresse email invalide")
            return value.lower().strip()
        return value
    
    def validate_note(self, value):
        """
        Validation de la note (1-5)
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être entre 1 et 5")
        return value
    
    def create(self, validated_data):
        """
        Création avec ajout d'informations de suivi
        """
        # Ajouter IP pour anti-spam
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self._get_client_ip(request)
        
        # Masquer le nom du client (ex: John D. → John D.)
        if 'client_nom' in validated_data:
            validated_data['nom_masque'] = self._masquer_nom(
                validated_data['client_nom']
            )
        
        return super().create(validated_data)
    
    def _get_client_ip(self, request):
        """
        Récupérer l'adresse IP du client
        """
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _masquer_nom(self, nom_complet):
        """
        Masquer partiellement le nom pour la confidentialité
        """
        parties = nom_complet.split()
        if len(parties) >= 2:
            return f"{parties[0]} {parties[1][0]}."
        return f"{nom_complet}"


class AvisClientSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des avis
    """
    nom_masque = serializers.CharField(read_only=True)
    sticker_nom = serializers.CharField(source='sticker.nom', read_only=True)
    date_formattee = serializers.CharField(source='get_date_formattee', read_only=True)
    
    class Meta:
        model = AvisClient
        fields = [
            'id', 'nom_masque', 'sticker', 'sticker_nom',
            'note', 'titre', 'commentaire', 'date_formattee',
            'utile_oui', 'utile_non', 'created_at'
        ]
        read_only_fields = fields


# ========================================
# 5. SERIALIZERS CODES PROMO
# ========================================

class CodePromoSerializer(serializers.ModelSerializer):
    """
    Serializer pour les codes promotionnels
    """
    valide = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CodePromo
        fields = [
            'id', 'code', 'description',
            'pourcentage_reduction', 'montant_fixe_reduction',
            'date_debut', 'date_expiration',
            'limite_utilisations', 'utilisations',
            'type_utilisateur', 'est_actif', 'valide'
        ]
        read_only_fields = ['id', 'utilisations', 'valide']
    
    def get_valide(self, obj):
        """
        Vérifier si le code promo est encore valide
        """
        now = timezone.now()
        return (
            obj.est_actif and
            obj.date_debut <= now <= obj.date_expiration and
            obj.utilisations < obj.limite_utilisations
        )


class CodePromoValidationSerializer(serializers.Serializer):
    """
    Serializer pour valider un code promo
    """
    code = serializers.CharField(max_length=20)
    type_utilisateur = serializers.ChoiceField(
        choices=['client_externe', 'notaire', 'admin'],
        default='client_externe'
    )
    
    def validate(self, data):
        """
        Validation du code promo
        """
        from .services import CodePromoService
        
        try:
            code_promo = CodePromoService.valider_code_promo(
                code=data['code'],
                type_utilisateur=data['type_utilisateur']
            )
            data['code_promo_obj'] = code_promo
            data['reduction'] = code_promo.pourcentage_reduction
        except DjangoValidationError as e:
            raise serializers.ValidationError({'code': str(e)})
        
        return data


# ========================================
# 6. SERIALIZERS STATISTIQUES
# ========================================

class StatistiquesPeriodSerializer(serializers.Serializer):
    """
    Serializer pour définir la période des statistiques
    """
    date_debut = serializers.DateField(required=False)
    date_fin = serializers.DateField(required=False)
    notaire_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        """
        Validation des dates
        """
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if date_debut and date_fin and date_debut > date_fin:
            raise serializers.ValidationError({
                'date_debut': 'La date de début doit être antérieure à la date de fin'
            })
        
        return data


# ========================================
# 7. SERIALIZERS STICKERS NOTAIRES
# ========================================

class ReferenceStickerSerializer(serializers.ModelSerializer):
    """
    Serializer pour les types de stickers disponibles
    """
    class Meta:
        model = ReferenceSticker
        fields = ['id', 'nom', 'description', 'image', 'prix_unitaire', 'total_stock', 'created_at']
        read_only_fields = ['created_at']

class VenteStickerNotaireSerializer(serializers.ModelSerializer):
    """
    Serializer pour les ventes de stickers aux notaires
    """
    notaire_nom = serializers.CharField(source='notaire.nom_complet', read_only=True)
    type_sticker_nom = serializers.CharField(source='type_sticker.nom', read_only=True)
    
    class Meta:
        model = VenteStickerNotaire
        fields = [
            'id', 'reference', 'notaire', 'notaire_nom',
            'type_sticker', 'type_sticker_nom',
            'quantite', 'plage_debut', 'plage_fin',
            'montant_total', 'montant_paye', 'reste_a_payer',
            'date_vente', 'created_at'
        ]

class RecuStickerSerializer(serializers.ModelSerializer):
    """
    Serializer pour le reçu de vente de stickers
    Format spécifique pour l'impression
    """
    numero = serializers.CharField(source='numero_recu')
    bpf = serializers.SerializerMethodField()
    date = serializers.DateField(source='date_recu')
    notaire = serializers.SerializerMethodField()
    lignes = serializers.SerializerMethodField()
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    montant_en_lettres = serializers.SerializerMethodField()

    class Meta:
        model = VenteStickerNotaire
        fields = [
            'id',
            'numero',
            'bpf',
            'date',
            'notaire',
            'mode_reglement',
            'lignes',
            'montant_total',
            'montant_en_lettres'
        ]

    def get_bpf(self, obj):
        """Montant total en entiers (pour affichage BPF)"""
        return int(obj.montant_total)

    def get_notaire(self, obj):
        notaire = obj.notaire
        return {
            "id": notaire.id,
            "nom": f"{notaire.nom} {notaire.prenom}",
            "adresse": notaire.adresse,
            "rscpm": notaire.rscpm or "N/A",
            "ifu": notaire.ifu or "N/A",
            "telephone": notaire.telephone
        }

    def get_lignes(self, obj):
        return [
            {
                "libelle": f"ACHAT DE {obj.type_sticker.nom.upper()}",
                "plage": f"{obj.plage_debut}-{obj.plage_fin}",
                "nombre": obj.quantite,
                "prix_unitaire": int(obj.type_sticker.prix_unitaire)
            }
        ]

    def get_montant_en_lettres(self, obj):
        """Conversion du montant en toutes lettres (version simplifiée)"""
        # Note: Pour une version de production parfaite, utiliser une lib comme num2words
        # Ici on fournit une version basique ou on laisse le frontend le faire si préféré.
        # Mais on va essayer de fournir une chaîne propre.
        try:
            from apps.core.utils import montant_en_lettres # Check if utility exists
            return montant_en_lettres(int(obj.montant_total))
        except ImportError:
            return f"{int(obj.montant_total)} francs CFA"

class RecuStickerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'une vente de sticker via l'API de reçus
    """
    notaire_id = serializers.IntegerField(write_only=True)
    reference_sticker_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = VenteStickerNotaire
        fields = [
            'notaire_id',
            'reference_sticker_id',
            'quantite',
            'plage_debut',
            'plage_fin',
            'mode_reglement',
            'date_vente'
        ]

    def create(self, validated_data):
        notaire_id = validated_data.pop('notaire_id', None)
        reference_sticker_id = validated_data.pop('reference_sticker_id', None)
        
        # Mappage vers les champs du modèle
        if notaire_id:
            validated_data['notaire_id'] = notaire_id
        if reference_sticker_id:
            validated_data['type_sticker_id'] = reference_sticker_id
        
        return super().create(validated_data)


class RecuVenteStickerSerializer(serializers.ModelSerializer):
    """
    Formate les données pour le reçu PDF du Frontend.
    """
    numero = serializers.SerializerMethodField()
    date_recu = serializers.SerializerMethodField()
    bpf = serializers.SerializerMethodField()
    notaire = serializers.SerializerMethodField()
    lignes = serializers.SerializerMethodField()
    mode_reglement = serializers.SerializerMethodField()

    class Meta:
        model = VenteSticker
        fields = ['numero', 'date_recu', 'bpf', 'notaire', 'lignes', 'mode_reglement']

    def get_numero(self, obj):
        # Format: REC-{ID}-ANNEE/ONBF
        # Utilisation de date_vente car created_at n'est pas explicite dans le modèle VenteSticker
        annee = obj.date_vente.year
        return f"REC-{obj.id:03d}-{annee}/ONBF"

    def get_date_recu(self, obj):
        return obj.date_vente.strftime("%d/%m/%Y")

    def get_bpf(self, obj):
        # Montant total
        return int(obj.montant_total)

    def get_notaire(self, obj):
        # Récupérer les infos du notaire lié
        notaire = obj.notaire
        if not notaire:
            return None
        return {
            "nom": f"{notaire.nom.upper()} {notaire.prenom}",
            "adresse": notaire.adresse or "Ouagadougou",
            "rscpm": notaire.rscpm or "",
            "ifu": notaire.ifu or "",
            "telephone": notaire.telephone or ""
        }

    def get_mode_reglement(self, obj):
        # Le modèle VenteSticker n'a pas de mode_reglement explicite, contrairement à VenteStickerNotaire
        # On met 'espece' par défaut ou on cherche un paiement lié
        return "espece"

    def get_lignes(self, obj):
        # Détails de la vente
        return [
            {
                "libelle": f"ACHAT DE {obj.sticker.nom.upper()}" if obj.sticker else "ACHAT DE STICKERS",
                "plage": "", # Plage non stockée dans VenteSticker (contrairement à VenteStickerNotaire)
                "nombre": obj.quantite,
                "prix_unitaire": int(obj.montant_total / obj.quantite) if obj.quantite > 0 else 0
            }
        ]


