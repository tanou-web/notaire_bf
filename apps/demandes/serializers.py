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
        return data

class DemandeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandesDemande
        fields = ['document', 'email_reception', 'donnees_formulaire']
    
    def create(self, validated_data):
        # Générer la référence
        import random
        from datetime import datetime
        validated_data['reference'] = f"DEM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        validated_data['utilisateur'] = self.context['request'].user
        validated_data['montant_total'] = validated_data['document'].prix
        validated_data['statut'] = 'brouillon'
        
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