import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class SystemEmailprofessionnel(models.Model):
    """
    Gestion des emails professionnels du domaine notarial.
    Les mots de passe NE SONT PAS stockés (sécurité).
    """

    class EmailRole(models.TextChoices):
        CONTACT = 'contact', _('Contact général')
        SECRETARIAT = 'secretariat', _('Secrétariat')
        DIRECTION = 'direction', _('Direction')
        SUPPORT = 'support', _('Support technique')
        FACTURATION = 'facturation', _('Facturation')
        JURIDIQUE = 'juridique', _('Juridique')
        ADMIN = 'admin', _('Administration')
        TECHNIQUE = 'technique', _('Technique')
        AUTRE = 'autre', _('Autre')

    class EmailProvider(models.TextChoices):
        GOOGLE = 'google', _('Google Workspace')
        ZOHO = 'zoho', _('Zoho Mail')
        CPANEL = 'cpanel', _('cPanel / Hébergeur')
        MICROSOFT = 'microsoft', _('Microsoft 365')
        AUTRE = 'autre', _('Autre')

    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name=_("Email professionnel"),
        help_text=_("Adresse email du domaine (ex: contact@notairesbf.com)")
    )

    role = models.CharField(
        max_length=50,
        choices=EmailRole.choices,
        verbose_name=_("Rôle fonctionnel"),
        help_text=_("Usage métier de cet email")
    )

    provider = models.CharField(
        max_length=50,
        choices=EmailProvider.choices,
        default=EmailProvider.AUTRE,
        verbose_name=_("Fournisseur email")
    )

    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_professionnels',
        verbose_name=_("Utilisateur associé"),
        help_text=_("Agent ou responsable utilisant cet email")
    )

    alias_pour = models.EmailField(
        blank=True,
        null=True,
        max_length=254,
        verbose_name=_("Alias de"),
        help_text=_("Email principal si cet email est un alias")
    )

    peut_envoyer = models.BooleanField(
        default=True,
        verbose_name=_("Peut envoyer"),
        help_text=_("Autorisé pour l'envoi de mails")
    )

    peut_recevoir = models.BooleanField(
        default=True,
        verbose_name=_("Peut recevoir"),
        help_text=_("Autorisé pour la réception de mails")
    )

    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Email actuellement utilisé")
    )

    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Ex: Email principal du secrétariat")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )

    class Meta:
        db_table = 'system_email_professionnel'
        verbose_name = _("Email professionnel")
        verbose_name_plural = _("Emails professionnels")
        ordering = ['role', 'email']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['actif']),
        ]

    def __str__(self):
        status = "Actif" if self.actif else "Inactif"
        return f"{self.email} ({self.get_role_display()} – {status})"

    def est_alias(self):
        return self.alias_pour is not None


class SystemConfig(models.Model):
    """
    Configuration système flexible et sécurisée.
    Supporte différents types de valeurs et catégories.
    """

    VALUE_TYPES = [
        ('string', _('Chaîne')),
        ('integer', _('Entier')),
        ('float', _('Nombre décimal')),
        ('boolean', _('Booléen')),
        ('json', _('JSON')),
        ('datetime', _('Date/Heure')),
        ('file', _('Fichier')),
    ]

    CATEGORIES = [
        ('general', _('Général')),
        ('security', _('Sécurité')),
        ('email', _('Email')),
        ('database', _('Base de données')),
        ('backup', _('Sauvegarde')),
        ('logging', _('Journalisation')),
        ('cache', _('Cache')),
        ('api', _('API')),
        ('integration', _('Intégration')),
        ('custom', _('Personnalisé')),
    ]

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
        choices=VALUE_TYPES,
        default='string',
        verbose_name=_("Type de valeur")
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORIES,
        default='general',
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
        blank=True,
        null=True,
        verbose_name=_("Valeur minimale")
    )

    max_value = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Valeur maximale")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )

    class Meta:
        db_table = 'system_config'
        verbose_name = _("Configuration système")
        verbose_name_plural = _("Configurations système")
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['key']),
            models.Index(fields=['is_public']),
            models.Index(fields=['is_editable']),
        ]

    def __str__(self):
        return f"{self.category}: {self.key}"

    def get_value(self):
        """Retourne la valeur typée selon value_type"""
        if self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'integer':
            try:
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        elif self.value_type == 'float':
            try:
                return float(self.value)
            except (ValueError, TypeError):
                return 0.0
        elif self.value_type == 'json':
            try:
                import json
                return json.loads(self.value)
            except (ValueError, TypeError):
                return {}
        return self.value

    def set_value(self, value):
        """Définit la valeur en la convertissant en string"""
        if isinstance(value, bool):
            self.value = 'true' if value else 'false'
            self.value_type = 'boolean'
        elif isinstance(value, (int, float)):
            self.value = str(value)
            self.value_type = 'integer' if isinstance(value, int) else 'float'
        elif isinstance(value, dict):
            import json
            self.value = json.dumps(value, ensure_ascii=False)
            self.value_type = 'json'
        else:
            self.value = str(value)
            self.value_type = 'string'


class SystemLog(models.Model):
    """
    Journal système pour le monitoring et l'audit.
    Enregistre toutes les actions importantes du système.
    """

    LEVEL_CHOICES = [
        ('debug', _('Debug')),
        ('info', _('Information')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
        ('critical', _('Critique')),
    ]

    SOURCE_CHOICES = [
        ('system', _('Système')),
        ('api', _('API')),
        ('database', _('Base de données')),
        ('auth', _('Authentification')),
        ('backup', _('Sauvegarde')),
        ('task', _('Tâche')),
        ('integration', _('Intégration')),
        ('security', _('Sécurité')),
    ]

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
        choices=LEVEL_CHOICES,
        default='info',
        verbose_name=_("Niveau")
    )

    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='system',
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
        blank=True,
        default=dict,
        verbose_name=_("Détails")
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("Adresse IP")
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent")
    )

    duration = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Durée (ms)"),
        help_text=_("Durée de l'opération en millisecondes")
    )

    is_resolved = models.BooleanField(
        default=False,
        verbose_name=_("Résolu")
    )

    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Résolu le")
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
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.level.upper()}: {self.message[:50]}..."


class MaintenanceWindow(models.Model):
    """
    Fenêtres de maintenance planifiées pour les interventions système.
    """

    MAINTENANCE_TYPES = [
        ('scheduled', _('Planifiée')),
        ('emergency', _('Urgence')),
        ('routine', _('Routine')),
    ]

    STATUS_CHOICES = [
        ('scheduled', _('Planifiée')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
    ]

    IMPACT_LEVELS = [
        ('low', _('Faible')),
        ('medium', _('Moyen')),
        ('high', _('Élevé')),
        ('critical', _('Critique')),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre")
    )

    description = models.TextField(
        verbose_name=_("Description")
    )

    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPES,
        default='scheduled',
        verbose_name=_("Type")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
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
        choices=IMPACT_LEVELS,
        default='medium',
        verbose_name=_("Niveau d'impact")
    )

    notification_sent = models.BooleanField(
        default=False,
        verbose_name=_("Notification envoyée")
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'system_maintenance'
        verbose_name = _("Fenêtre de maintenance")
        verbose_name_plural = _("Fenêtres de maintenance")
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class SystemMetric(models.Model):
    """
    Métriques système pour le monitoring des performances.
    """

    METRIC_TYPES = [
        ('cpu', _('CPU')),
        ('memory', _('Mémoire')),
        ('disk', _('Disque')),
        ('network', _('Réseau')),
        ('database', _('Base de données')),
        ('request', _('Requête')),
        ('response_time', _('Temps de réponse')),
        ('error_rate', _("Taux d'erreur")),
        ('custom', _('Personnalisé')),
    ]

    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPES,
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
        blank=True,
        default='',
        verbose_name=_("Unité")
    )

    tags = models.JSONField(
        blank=True,
        default=dict,
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
            models.Index(fields=['metric_type']),
            models.Index(fields=['collected_at']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}"


class APIKey(models.Model):
    """
    Clés API pour l'accès programmatique au système.
    """

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('revoked', _('Révoquée')),
        ('expired', _('Expirée')),
    ]

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
        choices=STATUS_CHOICES,
        default='active',
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
        blank=True,
        null=True,
        verbose_name=_("Expire le")
    )

    last_used = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Dernière utilisation")
    )

    total_requests = models.IntegerField(
        default=0,
        verbose_name=_("Total requêtes")
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'system_api_key'
        verbose_name = _("Clé API")
        verbose_name_plural = _("Clés API")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def is_expired(self):
        """Vérifie si la clé est expirée"""
        return self.expires_at and timezone.now() > self.expires_at

    @property
    def is_active(self):
        """Vérifie si la clé est active"""
        return self.status == 'active' and not self.is_expired


class ScheduledTask(models.Model):
    """
    Tâches planifiées pour l'automatisation système.
    """

    TASK_TYPES = [
        ('system', _('Système')),
        ('backup', _('Sauvegarde')),
        ('cleanup', _('Nettoyage')),
        ('report', _('Rapport')),
        ('sync', _('Synchronisation')),
        ('custom', _('Personnalisée')),
    ]

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('paused', _('En pause')),
        ('completed', _('Terminée')),
        ('failed', _('Échouée')),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom")
    )

    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPES,
        default='system',
        verbose_name=_("Type de tâche")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
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
        blank=True,
        default=dict,
        verbose_name=_("Arguments")
    )

    last_run = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Dernière exécution")
    )

    last_result = models.TextField(
        blank=True,
        verbose_name=_("Dernier résultat")
    )

    last_duration = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Dernière durée (ms)")
    )

    next_run = models.DateTimeField(
        blank=True,
        null=True,
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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'system_scheduled_task'
        verbose_name = _("Tâche planifiée")
        verbose_name_plural = _("Tâches planifiées")
        ordering = ['-next_run']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['task_type']),
            models.Index(fields=['is_enabled']),
            models.Index(fields=['next_run']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class SystemHealth(models.Model):
    """
    État de santé des différents services système.
    """

    STATUS_CHOICES = [
        ('healthy', _('Sain')),
        ('degraded', _('Dégradé')),
        ('unhealthy', _('Malsain')),
        ('unknown', _('Inconnu')),
    ]

    service = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Service")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown',
        verbose_name=_("Statut")
    )

    last_check = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Dernière vérification")
    )

    response_time = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Temps de réponse (ms)")
    )

    details = models.JSONField(
        blank=True,
        default=dict,
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
        indexes = [
            models.Index(fields=['service']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.service}: {self.get_status_display()}"


class SystemNotification(models.Model):
    """
    Notifications système pour alerter les administrateurs.
    """

    NOTIFICATION_TYPES = [
        ('info', _('Information')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
        ('success', _('Succès')),
        ('maintenance', _('Maintenance')),
        ('security', _('Sécurité')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Basse')),
        ('medium', _('Moyenne')),
        ('high', _('Haute')),
        ('urgent', _('Urgente')),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre")
    )

    message = models.TextField(
        verbose_name=_("Message")
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name=_("Type")
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
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
        blank=True,
        null=True,
        verbose_name=_("Acquitté le")
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Expire le")
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'system_notification'
        verbose_name = _("Notification système")
        verbose_name_plural = _("Notifications système")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_acknowledged']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"

    @property
    def is_expired(self):
        """Vérifie si la notification est expirée"""
        return self.expires_at and timezone.now() > self.expires_at