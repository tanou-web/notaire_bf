from rest_framework import serializers
from .models import DemandesDemande
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