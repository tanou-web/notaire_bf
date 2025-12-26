from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ActualitesActualite

User = get_user_model()


class ActualiteAuteurSerializer(serializers.ModelSerializer):
    """Serializer minimal pour l'auteur"""
    nom_complet = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'nom', 'prenom', 'nom_complet']
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}" if hasattr(obj, 'nom') else obj.username


class ActualiteSerializer(serializers.ModelSerializer):
    auteur_detail = ActualiteAuteurSerializer(source='auteur', read_only=True)
    categorie_display = serializers.CharField(source='categorie_display', read_only=True)
    est_publiee = serializers.SerializerMethodField()
    resume_auto = serializers.CharField(read_only=True)
    temps_lecture = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ActualitesActualite
        fields = [
            'id', 'titre', 'slug', 'contenu', 'resume', 'resume_auto',
            'categorie', 'categorie_display', 'image_principale', 'image_url',
            'auteur', 'auteur_detail', 'date_publication', 'important',
            'publie', 'est_publiee', 'vue', 'featured', 'temps_lecture',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['vue', 'slug', 'created_at', 'updated_at']
        extra_kwargs = {
            'date_publication': {'required': False},
        }
    
    def get_est_publiee(self, obj):
        return obj.est_publiee
    

    def get_temps_lecture(self, obj):
        """Calculer le temps de lecture estimé (250 mots/minute)"""
        mots = len(obj.contenu.split())
        minutes = max(1, mots // 250)  # au moins 1 minute
        return f"{minutes} min"
    
    def get_image_url(self, obj):
        """Générer l'URL complète de l'image"""
        request = self.context.get('request')
        if request and obj.image_principale:
            return request.build_absolute_uri(obj.image_principale)
        return obj.image_principale
    
    def validate(self, data):
        """Validation globale de l'actualité"""
        publie = data.get('publie', getattr(self.instance, 'publie', False))
        featured = data.get('featured', getattr(self.instance, 'feature', False))
        if featured and not publie:
            raise serializers.ValidationError(
                'Une actualité mise en avant doit être publiée'
            )
    
    def create(self, validated_data):
        """Création d'une actualité avec l'auteur courant"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and not validated_data.get('auteur'):
            validated_data['auteur'] = request.user
        
        # Par défaut, date de publication maintenant si publié
        if validated_data.get('publie', False) and not validated_data.get('date_publication'):
            validated_data['date_publication'] = timezone.now()
        
        return super().create(validated_data)


class ActualiteListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes"""
    auteur_nom = serializers.SerializerMethodField()
    categorie_display = serializers.CharField(source='get_categorie_display', read_only=True)
    temps_lecture = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ActualitesActualite
        fields = [
            'id', 'titre', 'slug', 'resume', 'categorie', 'categorie_display',
            'image_principale', 'image_url', 'auteur_nom', 'date_publication',
            'important', 'publie', 'vue', 'featured', 'temps_lecture',
            'created_at'
        ]

    def get_auteur_nom(self, obj):
        if obj.auteur:
            return f'{obj.auteur.nom}{obj.auteur.prenom}'.strip()
        return None
    
    def get_temps_lecture(self, obj):
        mots = len(obj.contenu.split())
        minutes = max(1, mots // 250)
        return minutes
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image_principale:
            return request.build_absolute_uri(obj.image_principale)
        return obj.image_principale