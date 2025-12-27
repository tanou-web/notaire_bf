from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()

class SystemConfig(models.Model):
    """Configuration système clé-valeur."""
    
    class ConfigCategory(models.TextChoices):
        GENERAL = 'general', _('Général')
        SECURITY = 'security', _('Sécurité')
        EMAIL = 'email', _('Email')
        DATABASE = 'database', _('Base de données')
        BACKUP = 'backup', _('Sauvegarde')
        LOGGING = 'logging', _('Journalisation')
        CACHE = 'cache', _('Cache')
        API = 'api', _('API')
        INTEGRATION = 'integration', _('Intégration')
        CUSTOM = 'custom', _('Personnalisé')
    
    class ValueType(models.TextChoices):
        STRING = 'string', _('Chaîne')
        INTEGER = 'integer', _('Entier')
        FLOAT = 'float', _('Nombre décimal')
        BOOLEAN = 'boolean', _('Booléen')
        JSON = 'json', _('JSON')
        DATETIME = 'datetime', _('Date/Heure')
        FILE = 'file', _('Fichier')
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Clé"),
        help_text=_("Clé unique de la configuration")
    )
    
    value = models.TextField(
        verbose_name=_("Valeur"),
        help_text=_("Valeur de la configuration")
    )
    
    value_type = models.CharField(
        max_length=20,
        choices=ValueType.choices,
        default=ValueType.STRING,
        verbose_name=_("Type de valeur")
    )
    
    category = models.CharField(
        max_length=50,
        choices=ConfigCategory.choices,
        default=ConfigCategory.GENERAL,
        verbose_name=_("Catégorie")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description de la configuration")
    )
    
    is_encrypted = models.BooleanField(
        default=False,
        verbose_name=_("Chiffré"),
        help_text=_("Si la valeur est chiffrée dans la base")
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Public"),
        help_text=_("Visible par tous les utilisateurs")
    )
    
    is_editable = models.BooleanField(
        default=True,
        verbose_name=_("Modifiable"),
        help_text=_("Peut être modifié via l'interface")
    )
    
    is_required = models.BooleanField(
        default=False,
        verbose_name=_("Requis"),
        help_text=_("Configuration obligatoire")
    )
    
    default_value = models.TextField(
        blank=True,
        verbose_name=_("Valeur par défaut")
    )
    
    validation_regex = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Regex de validation")
    )
    
    min_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Valeur minimale")
    )
    
    max_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Valeur maximale")
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Mis à jour le"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_configs',
        verbose_name=_("Créé par")
    )
    
    class Meta:
        db_table = 'system_config'
        verbose_name = _("Configuration système")
        verbose_name_plural = _("Configurations système")
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.category})"
    
    def get_value(self):
        """Retourne la valeur convertie selon son type."""
        if self.is_encrypted:
            # Décrypter la valeur (à implémenter selon votre système de chiffrement)
            from .services import EncryptionService
            raw_value = EncryptionService.decrypt(self.value)
        else:
            raw_value = self.value
        
        try:
            if self.value_type == self.ValueType.INTEGER:
                return int(raw_value)
            elif self.value_type == self.ValueType.FLOAT:
                return float(raw_value)
            elif self.value_type == self.ValueType.BOOLEAN:
                return raw_value.lower() in ('true', '1', 'yes', 'y', 'on')
            elif self.value_type == self.ValueType.JSON:
                return json.loads(raw_value)
            elif self.value_type == self.ValueType.DATETIME:
                return timezone.datetime.fromisoformat(raw_value)
            else:
                return raw_value
        except (ValueError, json.JSONDecodeError):
            return raw_value
    
    def set_value(self, value):
        """Définit la valeur avec conversion."""
        if self.value_type == self.ValueType.INTEGER:
            self.value = str(int(value))
        elif self.value_type == self.ValueType.FLOAT:
            self.value = str(float(value))
        elif self.value_type == self.ValueType.BOOLEAN:
            self.value = 'true' if value else 'false'
        elif self.value_type == self.ValueType.JSON:
            self.value = json.dumps(value)
        elif self.value_type == self.ValueType.DATETIME:
            if isinstance(value, str):
                self.value = value
            else:
                self.value = value.isoformat()
        else:
            self.value = str(value)
        
        if self.is_encrypted:
            from .services import EncryptionService
            self.value = EncryptionService.encrypt(self.value)
    
    def validate_value(self, value):
        """Valide la valeur selon les contraintes."""
        if self.validation_regex:
            import re
            if not re.match(self.validation_regex, str(value)):
                raise ValueError(f"La valeur ne correspond pas au format attendu: {self.validation_regex}")
        
        if self.min_value is not None:
            try:
                num_value = float(value)
                if num_value < self.min_value:
                    raise ValueError(f"La valeur doit être >= {self.min_value}")
            except ValueError:
                pass
        
        if self.max_value is not None:
            try:
                num_value = float(value)
                if num_value > self.max_value:
                    raise ValueError(f"La valeur doit être <= {self.max_value}")
            except ValueError:
                pass
        
        return True


class SystemLog(models.Model):
    """Journal des événements système."""
    
    class LogLevel(models.TextChoices):
        DEBUG = 'debug', _('Debug')
        INFO = 'info', _('Information')
        WARNING = 'warning', _('Avertissement')
        ERROR = 'error', _('Erreur')
        CRITICAL = 'critical', _('Critique')
    
    class LogSource(models.TextChoices):
        SYSTEM = 'system', _('Système')
        API = 'api', _('API')
        DATABASE = 'database', _('Base de données')
        AUTH = 'auth', _('Authentification')
        BACKUP = 'backup', _('Sauvegarde')
        TASK = 'task', _('Tâche')
        INTEGRATION = 'integration', _('Intégration')
        SECURITY = 'security', _('Sécurité')
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("UUID")
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Horodatage")
    )
    
    level = models.CharField(
        max_length=20,
        choices=LogLevel.choices,
        default=LogLevel.INFO,
        verbose_name=_("Niveau")
    )
    
    source = models.CharField(
        max_length=50,
        choices=LogSource.choices,
        default=LogSource.SYSTEM,
        verbose_name=_("Source")
    )
    
    module = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Module")
    )
    
    action = models.CharField(
        max_length=100,
        verbose_name=_("Action")
    )
    
    message = models.TextField(
        verbose_name=_("Message")
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Détails")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs',
        verbose_name=_("Utilisateur")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent")
    )
    
    duration = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Durée (ms)"),
        help_text=_("Durée de l'opération en millisecondes")
    )
    
    is_resolved = models.BooleanField(
        default=False,
        verbose_name=_("Résolu")
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Résolu le")
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_logs',
        verbose_name=_("Résolu par")
    )
    
    traceback = models.TextField(
        blank=True,
        verbose_name=_("Traceback")
    )
    
    class Meta:
        db_table = 'system_log'
        verbose_name = _("Journal système")
        verbose_name_plural = _("Journaux système")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['source']),
            models.Index(fields=['module']),
            models.Index(fields=['user']),
            models.Index(fields=['is_resolved']),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.module}: {self.message[:100]}"
    
    @classmethod
    def log(cls, level, source, module, action, message, **kwargs):
        """Méthode helper pour créer un log."""
        log = cls(
            level=level,
            source=source,
            module=module,
            action=action,
            message=message,
            **kwargs
        )
        log.save()
        return log


class MaintenanceWindow(models.Model):
    """Fenêtre de maintenance planifiée."""
    
    class MaintenanceType(models.TextChoices):
        SCHEDULED = 'scheduled', _('Planifiée')
        EMERGENCY = 'emergency', _('Urgence')
        ROUTINE = 'routine', _('Routine')
    
    class MaintenanceStatus(models.TextChoices):
        SCHEDULED = 'scheduled', _('Planifiée')
        IN_PROGRESS = 'in_progress', _('En cours')
        COMPLETED = 'completed', _('Terminée')
        CANCELLED = 'cancelled', _('Annulée')
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre")
    )
    
    description = models.TextField(
        verbose_name=_("Description")
    )
    
    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices,
        default=MaintenanceType.SCHEDULED,
        verbose_name=_("Type")
    )
    
    status = models.CharField(
        max_length=20,
        choices=MaintenanceStatus.choices,
        default=MaintenanceStatus.SCHEDULED,
        verbose_name=_("Statut")
    )
    
    start_time = models.DateTimeField(
        verbose_name=_("Heure de début")
    )
    
    end_time = models.DateTimeField(
        verbose_name=_("Heure de fin")
    )
    
    affected_services = models.JSONField(
        default=list,
        verbose_name=_("Services affectés")
    )
    
    impact_level = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Faible')),
            ('medium', _('Moyen')),
            ('high', _('Élevé')),
            ('critical', _('Critique')),
        ],
        default='medium',
        verbose_name=_("Niveau d'impact")
    )
    
    notification_sent = models.BooleanField(
        default=False,
        verbose_name=_("Notification envoyée")
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_maintenances',
        verbose_name=_("Créé par")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_maintenance'
        verbose_name = _("Fenêtre de maintenance")
        verbose_name_plural = _("Fenêtres de maintenance")
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.title} ({self.start_time.date()})"
    
    def is_active(self):
        """Vérifie si la maintenance est en cours."""
        now = timezone.now()
        return (
            self.status == self.MaintenanceStatus.IN_PROGRESS and
            self.start_time <= now <= self.end_time
        )
    
    def duration_hours(self):
        """Calcule la durée en heures."""
        duration = self.end_time - self.start_time
        return round(duration.total_seconds() / 3600, 2)


class SystemMetric(models.Model):
    """Métriques système pour le monitoring."""
    
    class MetricType(models.TextChoices):
        CPU = 'cpu', _('CPU')
        MEMORY = 'memory', _('Mémoire')
        DISK = 'disk', _('Disque')
        NETWORK = 'network', _('Réseau')
        DATABASE = 'database', _('Base de données')
        REQUEST = 'request', _('Requête')
        RESPONSE_TIME = 'response_time', _('Temps de réponse')
        ERROR_RATE = 'error_rate', _("Taux d'erreur")
        CUSTOM = 'custom', _('Personnalisé')
    
    metric_type = models.CharField(
        max_length=50,
        choices=MetricType.choices,
        verbose_name=_("Type de métrique")
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    
    value = models.FloatField(
        verbose_name=_("Valeur")
    )
    
    unit = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name=_("Unité")
    )
    
    tags = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Tags")
    )
    
    hostname = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Nom d'hôte")
    )
    
    collected_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Collecté à")
    )
    
    class Meta:
        db_table = 'system_metric'
        verbose_name = _("Métrique système")
        verbose_name_plural = _("Métriques système")
        ordering = ['-collected_at']
        indexes = [
            models.Index(fields=['metric_type', 'collected_at']),
            models.Index(fields=['name', 'collected_at']),
            models.Index(fields=['hostname']),
        ]
    
    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}"


class APIKey(models.Model):
    """Clés API pour l'authentification externe."""
    
    class KeyStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        REVOKED = 'revoked', _('Révoquée')
        EXPIRED = 'expired', _('Expirée')
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Clé")
    )
    
    secret = models.CharField(
        max_length=200,
        verbose_name=_("Secret")
    )
    
    status = models.CharField(
        max_length=20,
        choices=KeyStatus.choices,
        default=KeyStatus.ACTIVE,
        verbose_name=_("Statut")
    )
    
    permissions = models.JSONField(
        default=list,
        verbose_name=_("Permissions"),
        help_text=_("Liste des permissions accordées")
    )
    
    rate_limit = models.IntegerField(
        default=100,
        verbose_name=_("Limite de débit"),
        help_text=_("Requêtes par heure")
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expire le")
    )
    
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière utilisation")
    )
    
    total_requests = models.IntegerField(
        default=0,
        verbose_name=_("Total requêtes")
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_keys',
        verbose_name=_("Créé par")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_api_key'
        verbose_name = _("Clé API")
        verbose_name_plural = _("Clés API")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def is_valid(self):
        """Vérifie si la clé est valide."""
        if self.status != self.KeyStatus.ACTIVE:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = self.KeyStatus.EXPIRED
            self.save()
            return False
        
        return True


class ScheduledTask(models.Model):
    """Tâches planifiées (cron jobs)."""
    
    class TaskStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        PAUSED = 'paused', _('En pause')
        COMPLETED = 'completed', _('Terminée')
        FAILED = 'failed', _('Échouée')
    
    class TaskType(models.TextChoices):
        SYSTEM = 'system', _('Système')
        BACKUP = 'backup', _('Sauvegarde')
        CLEANUP = 'cleanup', _('Nettoyage')
        REPORT = 'report', _('Rapport')
        SYNC = 'sync', _('Synchronisation')
        CUSTOM = 'custom', _('Personnalisée')
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )
    
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.SYSTEM,
        verbose_name=_("Type de tâche")
    )
    
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.ACTIVE,
        verbose_name=_("Statut")
    )
    
    command = models.CharField(
        max_length=200,
        verbose_name=_("Commande"),
        help_text=_("Commande à exécuter")
    )
    
    schedule = models.CharField(
        max_length=100,
        verbose_name=_("Planification"),
        help_text=_("Expression cron ou intervalle")
    )
    
    arguments = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Arguments")
    )
    
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière exécution")
    )
    
    last_result = models.TextField(
        blank=True,
        verbose_name=_("Dernier résultat")
    )
    
    last_duration = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Dernière durée (ms)")
    )
    
    next_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Prochaine exécution")
    )
    
    max_retries = models.IntegerField(
        default=3,
        verbose_name=_("Tentatives max")
    )
    
    retry_count = models.IntegerField(
        default=0,
        verbose_name=_("Nombre de tentatives")
    )
    
    timeout = models.IntegerField(
        default=300,
        verbose_name=_("Timeout (secondes)")
    )
    
    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Activée")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_scheduled_task'
        verbose_name = _("Tâche planifiée")
        verbose_name_plural = _("Tâches planifiées")
        ordering = ['-next_run']
    
    def __str__(self):
        return f"{self.name} ({self.task_type})"
    
    def calculate_next_run(self):
        """Calcule la prochaine exécution."""
        from .services import TaskScheduler
        self.next_run = TaskScheduler.calculate_next_run(self.schedule)
        self.save()


class SystemHealth(models.Model):
    """État de santé du système."""
    
    service = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Service")
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', _('Sain')),
            ('degraded', _('Dégradé')),
            ('unhealthy', _('Malsain')),
            ('unknown', _('Inconnu')),
        ],
        default='unknown',
        verbose_name=_("Statut")
    )
    
    last_check = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Dernière vérification")
    )
    
    response_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Temps de réponse (ms)")
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Détails")
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Message d'erreur")
    )
    
    class Meta:
        db_table = 'system_health'
        verbose_name = _("Santé système")
        verbose_name_plural = _("Santés système")
        ordering = ['service']
    
    def __str__(self):
        return f"{self.service}: {self.status}"
    
    def is_healthy(self):
        return self.status == 'healthy'


class SystemNotification(models.Model):
    """Notifications système."""
    
    class NotificationType(models.TextChoices):
        INFO = 'info', _('Information')
        WARNING = 'warning', _('Avertissement')
        ERROR = 'error', _('Erreur')
        SUCCESS = 'success', _('Succès')
        MAINTENANCE = 'maintenance', _('Maintenance')
        SECURITY = 'security', _('Sécurité')
    
    class NotificationPriority(models.TextChoices):
        LOW = 'low', _('Basse')
        MEDIUM = 'medium', _('Moyenne')
        HIGH = 'high', _('Haute')
        URGENT = 'urgent', _('Urgente')
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre")
    )
    
    message = models.TextField(
        verbose_name=_("Message")
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name=_("Type")
    )
    
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
        verbose_name=_("Priorité")
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Lu")
    )
    
    is_acknowledged = models.BooleanField(
        default=False,
        verbose_name=_("Acquitté")
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Acquitté le")
    )
    
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_notifications',
        verbose_name=_("Acquitté par")
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expire le")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_notification'
        verbose_name = _("Notification système")
        verbose_name_plural = _("Notifications système")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.notification_type}] {self.title}"
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class SystemEmailprofessionnel(models.Model):
    """Gestion des 10 emails professionnels (selon livrables cahier des charges)"""
    
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name=_("Email professionnel"),
        help_text=_("Email du domaine professionnel (ex: contact@notairesbf.com)")
    )
    
    mot_de_passe = models.CharField(
        max_length=200,
        verbose_name=_("Mot de passe"),
        help_text=_("Mot de passe crypté pour l'accès à la boîte mail")
    )
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_professionnels',
        verbose_name=_("Utilisateur associé"),
        help_text=_("Utilisateur qui utilise cet email")
    )
    
    alias_pour = models.EmailField(
        blank=True,
        null=True,
        max_length=254,
        verbose_name=_("Alias pour"),
        help_text=_("Si cet email est un alias, indiquer l'email principal")
    )
    
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Si l'email est actuellement utilisé")
    )
    
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Usage prévu de cet email (ex: 'Contact général', 'Support technique')")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_emailprofessionnel'
        verbose_name = _("Email professionnel")
        verbose_name_plural = _("Emails professionnels")
        ordering = ['email']

    def __str__(self):
        return f"{self.email} ({'Actif' if self.actif else 'Inactif'})"
    
    def est_alias(self):
        """Vérifie si cet email est un alias"""
        return self.alias_pour is not None