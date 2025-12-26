# apps/notaires/serializers.py
from rest_framework import serializers
from .models import NotairesNotaire, Region, Ville
from apps.demandes.models import DemandesDemande

class VilleSerializer(serializers.ModelSerializer):
    """Serializer pour les villes"""
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code_postal']

class RegionSerializer(serializers.ModelSerializer):
    """Serializer pour les régions"""
    villes = VilleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Region
        fields = ['id', 'nom', 'code', 'villes']

class NotaireMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les listes (performant)"""
    region_nom = serializers.CharField(source='region.nom', read_only=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    
    class Meta:
        model = NotairesNotaire
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'photo',
            'telephone', 'email', 'region_nom', 'ville_nom',
            'adresse_cabinet', 'actif'
        ]

class NotaireSerializer(serializers.ModelSerializer):
    """Serializer complet pour les détails d'un notaire"""
    region_details = RegionSerializer(source='region', read_only=True)
    ville_details = VilleSerializer(source='ville', read_only=True)
    nombre_demandes = serializers.SerializerMethodField()
    demandes_en_cours = serializers.SerializerMethodField()
    taux_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = NotairesNotaire
        fields = [
            # Informations de base
            'id', 'matricule', 'nom', 'prenom', 'photo',
            'telephone', 'email', 'adresse_cabinet',
            
            # Localisation
            'region', 'region_details',
            'ville', 'ville_details',
            'geolocalisation',
            
            # Statut
            'actif', 'date_inscription', 'derniere_connexion',
            
            # Spécialités
            'specialites', 'langues_parlees',
            'horaires_cabinet', 'tarifs',
            'annees_experience',
            
            # Statistiques
            'total_ventes', 'total_cotisations',
            'nombre_demandes', 'demandes_en_cours',
            'taux_completion'
        ]
        read_only_fields = [
            'date_inscription', 'derniere_connexion',
            'total_ventes', 'total_cotisations'
        ]
    
    def get_nombre_demandes(self, obj):
        """Nombre total de demandes assignées"""
        return DemandesDemande.objects.filter(notaire=obj).count()
    
    def get_demandes_en_cours(self, obj):
        """Nombre de demandes en cours de traitement"""
        return DemandesDemande.objects.filter(
            notaire=obj, 
            statut='en_traitement'
        ).count()
    
    def get_taux_completion(self, obj):
        """Taux de complétion des demandes"""
        total = self.get_nombre_demandes(obj)
        if total == 0:
            return 0
        completes = DemandesDemande.objects.filter(
            notaire=obj,
            statut='document_envoye_email'
        ).count()
        return round((completes / total) * 100, 1)

class NotaireCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un notaire"""
    class Meta:
        model = NotairesNotaire
        fields = [
            'matricule', 'nom', 'prenom', 'photo',
            'telephone', 'email', 'adresse_cabinet',
            'region', 'ville', 'specialites',
            'langues_parlees', 'horaires_cabinet',
            'tarifs', 'annees_experience'
        ]
    
    def create(self, validated_data):
        # Générer automatiquement les champs manquants
        validated_data['actif'] = True
        return super().create(validated_data)

class NotaireUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un notaire"""
    class Meta:
        model = NotairesNotaire
        fields = [
            'nom', 'prenom', 'photo', 'telephone',
            'email', 'adresse_cabinet', 'region', 'ville',
            'specialites', 'langues_parlees', 'horaires_cabinet',
            'tarifs', 'annees_experience', 'actif'
        ]

class NotaireStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des notaires"""
    id = serializers.IntegerField()
    nom_complet = serializers.CharField()
    region = serializers.CharField(source='region.nom')
    ville = serializers.CharField(source='ville.nom')
    total_demandes = serializers.IntegerField()
    demandes_terminees = serializers.IntegerField()
    demandes_en_cours = serializers.IntegerField()
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    taux_completion = serializers.FloatField()
    derniere_activite = serializers.DateTimeField()