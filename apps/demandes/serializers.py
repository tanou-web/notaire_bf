from rest_framework import serializers
from .models import DemandesDemande, DemandesPieceJointe
from apps.documents.serializers import DocumentSerializer
from apps.utilisateurs.serializers import UserProfileSerializer
from apps.notaires.serializers import NotaireSerializer

class DemandeSerializer(serializers.ModelSerializer):
    document_details = DocumentSerializer(source='document', read_only=True)
    utilisateur_details = UserProfileSerializer(source='utilisateur', read_only=True)
    notaire_details = NotaireSerializer(source='notaire', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = DemandesDemande
        fields = '__all__'
        read_only_fields = [
            'reference', 'created_at', 'updated_at',
            'date_attribution', 'date_envoi_email'
        ]
    
    def validate(self, data):
        # Validation personnalisée
        if data.get('statut') == 'attente_paiement' and not data.get('montant_total'):
            raise serializers.ValidationError({
                "montant_total": "Le montant total est requis pour le statut attente_paiement"
            })
        
        # Validation pour Testament (demande de documents obligatoires)
        # On peut vérifier cela lors de la création ou mise à jour
        document = data.get('document')
        if document and "testament" in document.nom.lower():
            # Dans un vrai système, on vérifierait les pièces jointes associées
            # Ici on s'assure que l'utilisateur est informé que ces pièces sont requises
            pass
            
        return data

class DemandeCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une demande - permet les utilisateurs anonymes"""
    
    donnees_formulaire = serializers.JSONField(required=False, default=dict)
    
    class Meta:
        model = DemandesDemande
        fields = [
            'id', 'reference', 'document', 'email_reception', 
            'donnees_formulaire', 'lien_affiliation', 'statut', 
            'montant_total', 'created_at'
        ]
        read_only_fields = ['id', 'reference', 'statut', 'montant_total', 'created_at']
    
    def validate_email_reception(self, value):
        """Valider que l'email est fourni"""
        if not value:
            raise serializers.ValidationError("L'email de réception est requis pour les utilisateurs anonymes.")
        return value
    
    def create(self, validated_data):
        # Générer la référence unique
        import random
        from datetime import datetime
        while True:
            reference = f"DEM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            if not DemandesDemande.objects.filter(reference=reference).exists():
                break
        
        validated_data['reference'] = reference
        
        # Si l'utilisateur est authentifié, l'associer à la demande
        # Sinon, la demande reste anonyme (utilisateur = None)
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['utilisateur'] = user
        else:
            validated_data['utilisateur'] = None
        
        # Calculer le montant total avec la commission (3%)
        document = validated_data['document']
        montant_base = document.prix
        frais_commission = 0  # Commission supprimée
        validated_data['montant_total'] = montant_base
        validated_data['frais_commission'] = frais_commission
        
        # Statut initial : attente de formulaire (l'utilisateur doit remplir le formulaire)
        validated_data['statut'] = 'attente_formulaire'
        
        return super().create(validated_data)


class PieceJointeSerializer(serializers.ModelSerializer):
    """Serializer pour les pièces jointes"""
    fichier_url = serializers.SerializerMethodField()
    taille_formatee = serializers.CharField(source='taille_formatee', read_only=True)
    type_piece_display = serializers.CharField(source='get_type_piece_display', read_only=True)
    
    class Meta:
        model = DemandesPieceJointe
        fields = [
            'id', 'demande', 'type_piece', 'type_piece_display',
            'fichier', 'fichier_url', 'nom_original',
            'taille_fichier', 'taille_formatee', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'taille_fichier']
    
    def get_fichier_url(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None


class PieceJointeCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de pièces jointes"""
    
    class Meta:
        model = DemandesPieceJointe
        fields = ['demande', 'type_piece', 'fichier', 'description']
    
    def validate_fichier(self, value):
        """Valider le fichier uploadé"""
        max_size = 10 * 1024 * 1024  # 10 MB
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        
        if value.size > max_size:
            raise serializers.ValidationError("Le fichier est trop volumineux (max 10 MB)")
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Type de fichier non autorisé. Types acceptés: PDF, JPG, PNG"
            )
        
        return value