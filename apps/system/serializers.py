from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SystemConfig, SystemLog, MaintenanceWindow, SystemMetric,
    APIKey, ScheduledTask, SystemHealth, SystemNotification,
    SystemEmailprofessionnel
)
import json

User = get_user_model()


class SystemConfigSerializer(serializers.ModelSerializer):
    """Serializer pour les configurations système."""
    
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
        """Retourne la valeur décodée."""
        return obj.get_value()
    
    def validate(self, data):
        """Validation des données."""
        if 'value' in data:
            config = self.instance if self.instance else SystemConfig(**data)
            try:
                # Valider la valeur selon le type
                config.set_value(data['value'])
                config.validate_value(data['value'])
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError({'value': str(e)})
        
        return data
    
    def to_representation(self, instance):
        """Override pour gérer les valeurs chiffrées."""
        data = super().to_representation(instance)
        # Ne pas exposer les valeurs chiffrées
        if instance.is_encrypted and not self.context.get('show_encrypted', False):
            data['value'] = '********'
        return data


class SystemLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs système."""
    
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
        """Retourne le nom d'affichage de l'utilisateur."""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None
    
    def validate_details(self, value):
        """Valide que les détails sont du JSON valide."""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Les détails doivent être du JSON valide.")
        return value


class MaintenanceWindowSerializer(serializers.ModelSerializer):
    """Serializer pour les fenêtres de maintenance."""
    
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
        """Validation des dates de maintenance."""
        start_time = data.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = data.get('end_time', getattr(self.instance, 'end_time', None))
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': "L'heure de fin doit être après l'heure de début."
            })
        
        return data


class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer pour les métriques système."""
    
    class Meta:
        model = SystemMetric
        fields = [
            'id', 'metric_type', 'name', 'value', 'unit',
            'tags', 'hostname', 'collected_at'
        ]
        read_only_fields = ['id', 'collected_at']


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer pour les clés API."""
    
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
        read_only_fields = ['id', 'key', 'secret', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True}
        }
    
    def get_created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
    
    def get_is_valid(self, obj):
        return obj.is_valid()
    
    def create(self, validated_data):
        """Génère automatiquement la clé et le secret."""
        import secrets
        import string
        
        # Générer une clé unique
        key = f"sk_{secrets.token_hex(16)}"
        secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        validated_data['key'] = key
        validated_data['secret'] = secret
        
        return super().create(validated_data)


class ScheduledTaskSerializer(serializers.ModelSerializer):
    """Serializer pour les tâches planifiées."""
    
    class Meta:
        model = ScheduledTask
        fields = [
            'id', 'name', 'task_type', 'status', 'command', 'schedule',
            'arguments', 'last_run', 'last_result', 'last_duration',
            'next_run', 'max_retries', 'retry_count', 'timeout',
            'is_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'last_result', 'last_duration', 'created_at', 'updated_at']


class SystemHealthSerializer(serializers.ModelSerializer):
    """Serializer pour la santé du système."""
    
    class Meta:
        model = SystemHealth
        fields = [
            'id', 'service', 'status', 'last_check',
            'response_time', 'details', 'error_message'
        ]
        read_only_fields = ['id']


class SystemNotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications système."""
    
    acknowledged_by_display = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'is_read', 'is_acknowledged', 'acknowledged_at',
            'acknowledged_by', 'acknowledged_by_display', 'expires_at',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_acknowledged_by_display(self, obj):
        if obj.acknowledged_by:
            return obj.acknowledged_by.get_full_name() or obj.acknowledged_by.username
        return None
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class SystemStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques système."""
    
    total_logs = serializers.IntegerField()
    logs_by_level = serializers.DictField()
    logs_by_source = serializers.DictField()
    active_maintenance = serializers.IntegerField()
    system_health = serializers.DictField()
    api_keys_active = serializers.IntegerField()
    scheduled_tasks = serializers.DictField()
    disk_usage = serializers.DictField()
    memory_usage = serializers.DictField()
    cpu_usage = serializers.FloatField()
    last_updated = serializers.DateTimeField()


class SystemAlertSerializer(serializers.Serializer):
    """Serializer pour les alertes système."""
    
    type = serializers.CharField()
    severity = serializers.CharField()
    message = serializers.CharField()
    service = serializers.CharField()
    timestamp = serializers.DateTimeField()
    details = serializers.DictField()
    action_required = serializers.BooleanField()


class SystemEmailprofessionnelSerializer(serializers.ModelSerializer):
    """Serializer pour les emails professionnels."""
    
    utilisateur_display = serializers.SerializerMethodField()
    est_alias = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SystemEmailprofessionnel
        fields = [
            'id', 'email', 'mot_de_passe', 'utilisateur', 'utilisateur_display',
            'alias_pour', 'actif', 'description', 'est_alias',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'mot_de_passe': {'write_only': True}
        }
    
    def get_utilisateur_display(self, obj):
        if obj.utilisateur:
            return f"{obj.utilisateur.nom} {obj.utilisateur.prenom}" or obj.utilisateur.username
        return None()