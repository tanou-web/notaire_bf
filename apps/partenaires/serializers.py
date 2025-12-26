from rest_framework import serializers
from .models import PartenairesPartenaire


class PartenaireSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = PartenairesPartenaire
        fields = ['id', 'nom', 'type_partenaire', 'logo', 'logo_url', 'url', 'description', 'ordre', 'actif', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_logo_url(self, obj):
        logo = getattr(obj, 'logo', None)
        if not logo:
            return None
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(logo)
        return logo
