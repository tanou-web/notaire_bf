from rest_framework import serializers
from .models import DocumentsDocument, DocumentsTextelegal


class DocumentSerializer(serializers.ModelSerializer):
    delai_heures_display = serializers.CharField(source='get_delai_heures_display', read_only=True)
    prix_formate = serializers.SerializerMethodField()
    fichier_url = serializers.SerializerMethodField()
    class Meta:
        model = DocumentsDocument
        fields = [
            'id', 'reference', 'nom', 'description', 
            'prix', 'prix_formate', 'delai_heures', 'delai_heures_display',
            'actif', 'created_at', 'updated_at','fichier',          
            'fichier_url', 
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_prix_formate(self, obj):
        """Formater le prix avec devise"""
        return f"{obj.prix:,} FCFA".replace(",", " ")
    
    def validate_delai_heures(self, value):
        if value != 120:
            raise serializers.ValidationError("Le délai doit être de 5 jours (120 heures)")
        return value
    
    def get_fichier_url(self, obj):
        """Générer l'URL complète du fichier"""
        request = self.context.get('request')
        if obj.fichier and obj.fichier.url:
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None


class TexteLegalSerializer(serializers.ModelSerializer):
    type_texte_display = serializers.CharField(source='get_type_texte_display', read_only=True)
    fichier_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentsTextelegal
        fields = [
            'id', 'type_texte', 'type_texte_display', 'reference',
            'titre', 'fichier', 'fichier_url', 'date_publication',
            'ordre', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_fichier_url(self, obj):
        """Générer l'URL complète du fichier"""
        request = self.context.get('request')
        if obj.fichier and obj.fichier.url:
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None
       
    
    def validate_type_texte(self, value):
        """Validation du type de texte"""
        valid_types = ['loi', 'decret', 'arrete', 'reglement_interieur']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Type de texte invalide. Doit être parmi: {', '.join(valid_types)}"
            )
        return value