from rest_framework import serializers
from .models import ContactInformations, ContactMessage


class ContactInformationSerializer(serializers.ModelSerializer):
	type_display = serializers.CharField(source='get_type_display', read_only=True)
	
	class Meta:
		model = ContactInformations
		fields = [
			'id', 'type', 'type_display', 'valeur',
			'latitude', 'longitude', 'ordre', 'actif',
			'created_at', 'updated_at'
		]
		read_only_fields = ['created_at', 'updated_at']


class ContactMessageCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = ContactMessage
		fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'sent', 'error', 'created_at']
		read_only_fields = ['id', 'sent', 'error', 'created_at']

	def validate(self, attrs):
		# basic validation: name, email, subject, message required by serializer field definitions
		return attrs
