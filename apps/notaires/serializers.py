# apps/notaires/serializers.py - COPIER-COLLER CE CODE
from rest_framework import serializers
from .models import NotairesNotaire, NotairesCotisation, NotairesStagiaire

class NotaireMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les listes (performant)"""
    region_nom = serializers.CharField(source='region.nom', read_only=True, allow_null=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True, allow_null=True)
    nom_complet = serializers.SerializerMethodField()
    
    class Meta:
        model = NotairesNotaire
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'photo',
            'telephone', 'email', 'region_nom', 'ville_nom',
            'adresse'
        ]
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"

class NotaireSerializer(serializers.ModelSerializer):
    """Serializer complet pour les détails d'un notaire"""
    region_nom = serializers.CharField(source='region.nom', read_only=True, allow_null=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True, allow_null=True)
    nom_complet = serializers.SerializerMethodField()
    nombre_demandes = serializers.SerializerMethodField()
    demandes_en_cours = serializers.SerializerMethodField()
    assurance_rc_valide = serializers.BooleanField(read_only=True)

    class Meta:
        model = NotairesNotaire
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet', 'photo',
            'telephone', 'email', 'adresse',
            'region', 'region_nom',
            'ville', 'ville_nom',
            'actif', 'created_at', 'updated_at',
            'total_ventes', 'total_cotisations',
            'nombre_demandes', 'demandes_en_cours',
            'assurance_rc_date_echeance', 'assurance_rc_valide'
        ]
        read_only_fields = [
            'created_at', 'updated_at',
            'total_ventes', 'total_cotisations'
        ]
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"
    
    def get_nombre_demandes(self, obj):
        try:
            from apps.demandes.models import DemandesDemande
            return DemandesDemande.objects.filter(notaire=obj).count()
        except ImportError:
            return 0

    def get_demandes_en_cours(self, obj):
        try:
            from apps.demandes.models import DemandesDemande
            return DemandesDemande.objects.filter(
                notaire=obj,
                statut__in=['en_traitement', 'en_attente_notaire']
            ).count()
        except ImportError:
            return 0

class NotaireCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotairesNotaire
        fields = [
            'matricule', 'nom', 'prenom', 'photo',
            'telephone', 'email', 'adresse',
            'region', 'ville',
            'assurance_rc_date_echeance',
            'assurance_rc_a_jour',  # ajouté
            'actif'                 # ajouté
        ]

    def create(self, validated_data):
        validated_data.setdefault('actif', True)          # s’il n’est pas envoyé
        validated_data.setdefault('assurance_rc_a_jour', False)  # défaut
        return super().create(validated_data)



class NotaireUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotairesNotaire
        fields = [
            'nom', 'prenom', 'photo', 'telephone',
            'email', 'adresse', 'region', 'ville',
            'actif',
            'assurance_rc_date_echeance'
        ]


class NotaireStatsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom_complet = serializers.CharField()
    matricule = serializers.CharField()
    region = serializers.CharField(source='region.nom', allow_null=True)
    ville = serializers.CharField(source='ville.nom', allow_null=True)
    total_demandes = serializers.IntegerField(default=0)
    demandes_terminees = serializers.IntegerField(default=0)
    demandes_en_cours = serializers.IntegerField(default=0)
    montant_total_ventes = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_completion = serializers.FloatField(default=0)
    derniere_activite = serializers.DateTimeField(allow_null=True)

class CotisationSerializer(serializers.ModelSerializer):
    notaire_nom = serializers.SerializerMethodField()
    notaire_matricule = serializers.CharField(source='notaire.matricule', read_only=True)

    class Meta:
        model = NotairesCotisation
        fields = [
            'id', 'notaire', 'notaire_nom', 'notaire_matricule',
            'annee', 'montant', 'statut', 'date_paiement',
            'created_at', 'updated_at'
        ]

    def get_notaire_nom(self, obj):
        return f"{obj.notaire.nom} {obj.notaire.prenom}"


class StagiaireSerializer(serializers.ModelSerializer):
    notaire_nom = serializers.CharField(
        source='notaire_maitre.nom',
        read_only=True
    )
    notaire_prenom = serializers.CharField(
        source='notaire_maitre.prenom',
        read_only=True
    )
    notaire_nom_complet = serializers.SerializerMethodField()

    class Meta:
        model = NotairesStagiaire
        fields = [
            'id',
            'notaire_maitre',
            'notaire_nom',
            'notaire_prenom',
            'notaire_nom_complet',
            'nom',
            'prenom',
            'email',
            'telephone',
            'statut',
            'date_debut',
            'date_fin_prevue',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_notaire_nom_complet(self, obj):
        if obj.notaire_maitre:
            return f"{obj.notaire_maitre.nom} {obj.notaire_maitre.prenom}"
        return None
