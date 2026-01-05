from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SystemConfig,
    SystemLog,
    MaintenanceWindow,
    SystemMetric,
    APIKey,
    ScheduledTask,
    SystemHealth,
    SystemNotification,
    SystemEmailprofessionnel,
)
import json

User = get_user_model()

# -----------------------------
# SYSTEM CONFIGURATION
# -----------------------------
class SystemConfigSerializer(serializers.ModelSerializer):
    current_value = serializers.SerializerMethodField()

    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'value_type', 'category', 'description',
            'is_encrypted', 'is_public', 'is_editable', 'is_required',
            'default_value', 'validation_regex', 'min_value', 'max_value',
            'current_value', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_current_value(self, obj):
        return obj.get_value()

    def validate(self, data):
        if 'value' in data:
            config = self.instance if self.instance else SystemConfig(**data)
            try:
                config.set_value(data['value'])
                config.validate_value(data['value'])
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError({'value': str(e)})
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_encrypted and not self.context.get('show_encrypted', False):
            data['value'] = '********'
        return data

# -----------------------------
# SYSTEM LOG
# -----------------------------
class SystemLogSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = SystemLog
        fields = [
            'id', 'uuid', 'timestamp', 'level', 'source', 'module',
            'action', 'message', 'details', 'user', 'user_display',
            'ip_address', 'user_agent', 'duration', 'is_resolved',
            'resolved_at', 'resolved_by', 'traceback'
        ]
        read_only_fields = ['id', 'uuid', 'timestamp']

    def get_user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None

    def validate_details(self, value):
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Les détails doivent être du JSON valide.")
        return value

# -----------------------------
# MAINTENANCE WINDOW
# -----------------------------
class MaintenanceWindowSerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceWindow
        fields = [
            'id', 'title', 'description', 'maintenance_type', 'status',
            'start_time', 'end_time', 'affected_services', 'impact_level',
            'notification_sent', 'is_active', 'duration_hours',
            'created_by', 'created_by_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_is_active(self, obj):
        return obj.is_active()

    def get_duration_hours(self, obj):
        return obj.duration_hours()

    def validate(self, data):
        start = data.get('start_time', getattr(self.instance, 'start_time', None))
        end = data.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and start >= end:
            raise serializers.ValidationError("La date de fin doit être postérieure au début.")
        return data

# -----------------------------
# SYSTEM METRIC
# -----------------------------
class SystemMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMetric
        fields = '__all__'
        read_only_fields = ['id', 'collected_at']

# -----------------------------
# API KEY
# -----------------------------
class APIKeySerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = APIKey
        fields = [
            'id', 'name', 'key', 'secret', 'status', 'permissions',
            'rate_limit', 'expires_at', 'last_used', 'total_requests',
            'is_valid', 'created_by', 'created_by_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']
        extra_kwargs = {'secret': {'write_only': True}}

    def get_created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_is_valid(self, obj):
        return obj.is_valid()

    def create(self, validated_data):
        import secrets, string
        validated_data['key'] = f"sk_{secrets.token_hex(16)}"
        validated_data['secret'] = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )
        return super().create(validated_data)

# -----------------------------
# SCHEDULED TASK
# -----------------------------
class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = '__all__'
        read_only_fields = [
            'id', 'last_run', 'last_result',
            'last_duration', 'created_at', 'updated_at'
        ]

# -----------------------------
# SYSTEM HEALTH
# -----------------------------
class SystemHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemHealth
        fields = '__all__'
        read_only_fields = ['id']

# -----------------------------
# SYSTEM NOTIFICATION
# -----------------------------
class SystemNotificationSerializer(serializers.ModelSerializer):
    acknowledged_by_display = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = SystemNotification
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_acknowledged_by_display(self, obj):
        if obj.acknowledged_by:
            return obj.acknowledged_by.get_full_name() or obj.acknowledged_by.username
        return None

    def get_is_expired(self, obj):
        return obj.is_expired()

# -----------------------------
# SYSTEM EMAIL PROFESSIONNEL
# -----------------------------
class SystemEmailprofessionnelSerializer(serializers.ModelSerializer):
    utilisateur_display = serializers.SerializerMethodField()
    est_alias = serializers.SerializerMethodField()

    class Meta:
        model = SystemEmailprofessionnel
        fields = [
            'id', 'email', 'mot_de_passe', 'utilisateur', 'utilisateur_display',
            'alias_pour', 'actif', 'description', 'est_alias',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'mot_de_passe': {'write_only': True}}

    def get_utilisateur_display(self, obj):
        if obj.utilisateur:
            return obj.utilisateur.get_full_name() or obj.utilisateur.username
        return None

    def get_est_alias(self, obj):
        return obj.est_alias()

# Ajouter à la fin de ton serializers.py
from rest_framework import serializers

class SystemStatsSerializer(serializers.Serializer):
    total_utilisateurs = serializers.IntegerField()
    total_demandes = serializers.IntegerField()
    total_documents = serializers.IntegerField()
    total_actifs = serializers.IntegerField()
from rest_framework import serializers

class SystemAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    titre = serializers.CharField()
    message = serializers.CharField()
    niveau = serializers.CharField()  # ex: 'info', 'warning', 'critical'
    date_creation = serializers.DateTimeField()
    est_resolu = serializers.BooleanField(default=False)
