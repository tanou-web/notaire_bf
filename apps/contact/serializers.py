from rest_framework import serializers
from .models import ContactInformations, ContactMessage


class ContactInformationSerializer(serializers.ModelSerializer):
	class Meta:
		model = ContactInformations
		fields = ['id', 'type', 'valeur', 'ordre', 'actif']


class ContactMessageCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = ContactMessage
		fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'sent', 'error', 'created_at']
		read_only_fields = ['id', 'sent', 'error', 'created_at']

	def validate(self, attrs):
		# basic validation: name, email, subject, message required by serializer field definitions
		return attrs
