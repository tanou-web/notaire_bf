# apps/core/serializers.py
from rest_framework import serializers
from .models import CoreConfiguration, CorePage


class CoreConfigurationSerializer(serializers.ModelSerializer):
    """Serializer pour la configuration système"""
    
    class Meta:
        model = CoreConfiguration
        fields = ['id', 'cle', 'valeur', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CorePageSerializer(serializers.ModelSerializer):
    """Serializer pour les pages CMS"""
    image_url = serializers.SerializerMethodField()
    url = serializers.CharField(source='url', read_only=True)
    
    class Meta:
        model = CorePage
        fields = [
            'id', 'titre', 'slug', 'contenu', 'resume',
            'template', 'meta_title', 'meta_description',
            'image_principale', 'image_url', 'url',
            'ordre', 'publie', 'date_publication',
            'auteur', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'url']
    
    def get_image_url(self, obj):
        if obj.image_principale:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_principale.url)
            return obj.image_principale.url
        return None


class CorePageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de pages"""
    
    class Meta:
        model = CorePage
        fields = [
            'titre', 'slug', 'contenu', 'resume',
            'template', 'meta_title', 'meta_description',
            'image_principale', 'ordre', 'publie', 'date_publication'
        ]

