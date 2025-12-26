# apps/organisation/serializers.py
from rest_framework import serializers
from .models import OrganisationMembrebureau

class MembreBureauMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les listes"""
    nom_complet = serializers.SerializerMethodField()
    poste_display = serializers.CharField(source='get_poste_display', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganisationMembrebureau
        fields = [
            'id', 'nom', 'prenom', 'nom_complet',
            'poste', 'poste_display', 'photo_url',
            'ordre', 'actif'
        ]
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

class MembreBureauSerializer(serializers.ModelSerializer):
    """Serializer complet pour les détails"""
    nom_complet = serializers.SerializerMethodField()
    poste_display = serializers.CharField(source='get_poste_display', read_only=True)
    photo_url = serializers.SerializerMethodField()
    est_en_mandat = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OrganisationMembrebureau
        fields = [
            'id', 'nom', 'prenom', 'nom_complet',
            'poste', 'poste_display',
            'photo', 'photo_url',
            'ordre', 'actif',
            'telephone', 'email', 'biographie',
            'date_entree', 'date_sortie',
            'mandat_debut', 'mandat_fin',
            'est_en_mandat',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

class MembreBureauCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création"""
    class Meta:
        model = OrganisationMembrebureau
        fields = [
            'nom', 'prenom', 'poste', 'photo',
            'ordre', 'actif', 'telephone', 'email',
            'biographie', 'date_entree', 'date_sortie',
            'mandat_debut', 'mandat_fin'
        ]

class MembreBureauUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour"""
    class Meta:
        model = OrganisationMembrebureau
        fields = [
            'nom', 'prenom', 'poste', 'photo',
            'ordre', 'actif', 'telephone', 'email',
            'biographie', 'date_entree', 'date_sortie',
            'mandat_debut', 'mandat_fin'
        ]

class BureauStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du bureau"""
    total_membres = serializers.IntegerField()
    membres_actifs = serializers.IntegerField()
    membres_en_mandat = serializers.IntegerField()
    repartition_par_poste = serializers.DictField()
    anciennete_moyenne = serializers.FloatField(help_text="En années")