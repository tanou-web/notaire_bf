from rest_framework import serializers
from .models import SecurityLog, LoginAttemptLog, TokenUsageLog, AuditAdminactionlog


class SecurityLogSerializer(serializers.ModelSerializer):
	user_email = serializers.CharField(source='user.email', read_only=True)

	class Meta:
		model = SecurityLog
		fields = [
			'id', 'user', 'user_email', 'action', 'ip_address', 'user_agent',
			'status_code', 'details', 'timestamp'
		]
		read_only_fields = fields


class LoginAttemptLogSerializer(serializers.ModelSerializer):
	user_email = serializers.CharField(source='user.email', read_only=True)

	class Meta:
		model = LoginAttemptLog
		fields = [
			'id', 'user', 'user_email', 'username', 'ip_address', 'success',
			'failure_reason', 'user_agent', 'timestamp'
		]
		read_only_fields = fields


class TokenUsageLogSerializer(serializers.ModelSerializer):
	user_email = serializers.CharField(source='user.email', read_only=True)

	class Meta:
		model = TokenUsageLog
		fields = [
			'id', 'user', 'user_email', 'token_type', 'action', 'token_id',
			'ip_address', 'used_at'
		]
		read_only_fields = fields


class AuditAdminActionSerializer(serializers.ModelSerializer):
	utilisateur_email = serializers.CharField(source='utilisateur.email', read_only=True)

	class Meta:
		model = AuditAdminactionlog
		fields = [
			'id', 'utilisateur', 'utilisateur_email', 'action', 'modele', 'instance_id',
			'anciennes_valeurs', 'nouvelles_valeurs', 'ip_address', 'user_agent', 'created_at'
		]
		read_only_fields = fields
