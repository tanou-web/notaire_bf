from django.conf import settings
from rest_framework import serializers
from .models import NotairesNotaire


class NotaireSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(source='region.nom', read_only=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = NotairesNotaire
        fields = ['id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 'region', 'region_nom', 'ville', 'ville_nom', 'adresse', 'photo', 'photo_url', 'actif', 'total_ventes', 'total_cotisations']

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        
        if obj.photo.startswith('http'):
            return obj.photo
        
        request = self.context.get('request')
        media_url = settings.MEDIA_URL.rstrip('/')

        if request:
            return request.build_absolute_uri(f'{media_url}/{obj.photo.lstrip('/')}')
        return f'{media_url}/{obj.photo.lstrip('/')}'
