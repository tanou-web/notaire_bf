from rest_framework import serializers
from .models import Evenement, Inscription

class EvenementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = '__all__'

class InscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscription
        fields = '__all__'
    
    def validate(self, data):
        # Validation custom si besoin
        return data
