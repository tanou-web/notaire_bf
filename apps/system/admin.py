from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SystemConfig, SystemLog, MaintenanceWindow, SystemMetric,
    APIKey, ScheduledTask, SystemHealth, SystemNotification
)


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'category', 'value_type', 'is_public', 'is_editable', 'created_at')
    list_filter = ('category', 'value_type', 'is_public', 'is_editable')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations de base', {
            'fields': ('key', 'value', 'value_type', 'category', 'description')
        }),
        ('Paramètres', {
            'fields': ('is_encrypted', 'is_public', 'is_editable', 'is_required')
        }),
        ('Validation', {
            'fields': ('default_value', 'validation_regex', 'min_value', 'max_value')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'level_display', 'source', 'module', 'action', 'user_display', 'is_resolved')
    list_filter = ('level', 'source', 'module', 'is_resolved', 'timestamp')
    search_fields = ('action', 'message', 'user__username', 'ip_address')
    readonly_fields = ('uuid', 'timestamp', 'details_formatted')
    date_hierarchy = 'timestamp'
    
    def level_display(self, obj):
        colors = {
            'debug': 'gray',
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred',
        }
        color = colors.get(obj.level, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_level_display())
    level_display.short_description = 'Niveau'
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return '-'
    user_display.short_description = 'Utilisateur'
    
    def details_formatted(self, obj):
        import json
        try:
            details = json.dumps(obj.details, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', details)
        except:
            return str(obj.details)
    details_formatted.short_description = 'Détails (formaté)'


@admin.register(MaintenanceWindow)
class MaintenanceWindowAdmin(admin.ModelAdmin):
    list_display = ('title', 'maintenance_type', 'status', 'start_time', 'end_time', 'is_active_display')
    list_filter = ('maintenance_type', 'status', 'impact_level')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def is_active_display(self, obj):
        if obj.is_active():
            return format_html('<span style="color: red;">● Actif</span>')
        return format_html('<span style="color: green;">○ Inactif</span>')
    is_active_display.short_description = 'Statut'


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'key_truncated', 'status', 'expires_at', 'last_used', 'total_requests')
    list_filter = ('status',)
    search_fields = ('name', 'key')
    readonly_fields = ('key', 'secret', 'created_at', 'updated_at', 'last_used')
    
    def key_truncated(self, obj):
        return f"{obj.key[:10]}...{obj.key[-6:]}"
    key_truncated.short_description = 'Clé'


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'status', 'is_enabled', 'last_run', 'next_run')
    list_filter = ('task_type', 'status', 'is_enabled')
    search_fields = ('name', 'command')
    readonly_fields = ('last_run', 'last_result', 'last_duration', 'created_at', 'updated_at')


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ('service', 'status_display', 'last_check', 'response_time')
    list_filter = ('status',)
    search_fields = ('service',)
    
    def status_display(self, obj):
        colors = {
            'healthy': 'green',
            'degraded': 'orange',
            'unhealthy': 'red',
            'unknown': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Statut'


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'priority', 'is_read', 'is_acknowledged', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'is_acknowledged')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'updated_at')


# Enregistrement du modèle SystemMetric si nécessaire
admin.site.register(SystemMetric)