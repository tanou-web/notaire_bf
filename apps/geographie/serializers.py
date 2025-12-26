from rest_framework import serializers
from .models import GeographieRegion, GeographieVille

class RegionSerializer(serializers.ModelSerializer):
    ville_count = serializers.SerializerMethodField()
    class Meta:
        model = GeographieRegion
        fields = [
            'id', 'nom', 'code','description',
            'ordre', 'ville_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at'
        ]
    def get_ville_count(self, obj):
        return obj.geographieville_set.count()
    
class VilleSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(source='region.nom', read_only=True)
    region_code = serializers.CharField(source='region.code', read_only=True)
    class Meta:
        model = GeographieVille
        fields = [
            'id', 'nom', 'code_postal',
            'region', 'region_nom','region_code',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at'
        ]