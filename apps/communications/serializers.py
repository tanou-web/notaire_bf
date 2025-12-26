from rest_framework import serializers
from .models import CommunicationsEmaillog


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()


class CommunicationsEmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationsEmaillog
        # expose core fields
        fields = [
            'id', 'type_email', 'destinataire', 'sujet', 'contenu', 'statut', 'message_id', 'erreur', 'created_at', 'updated_at'
        ]