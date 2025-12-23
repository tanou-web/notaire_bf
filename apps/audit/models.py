# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AuditAdminactionlog(models.Model):
    utilisateur = models.ForeignKey('UtilisateursUser', models.DO_NOTHING, blank=True, null=True)
    action = models.CharField(max_length=100)
    modele = models.CharField(max_length=50, blank=True, null=True)
    instance_id = models.IntegerField(blank=True, null=True)
    anciennes_valeurs = models.JSONField(blank=True, null=True)
    nouvelles_valeurs = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'audit_adminactionlog'


class SecurityLog(models.Model):
    """Journal de sécurité pour toutes les actions critiques"""
    
    ACTION_CHOICES = [
        ('login_success', 'Connexion réussie'),
        ('login_failed', 'Connexion échouée'),
        ('logout', 'Déconnexion'),
        ('register', 'Inscription'),
        ('email_verify_send', 'Envoi vérification email'),
        ('email_verify_success', 'Vérification email réussie'),
        ('email_verify_failed', 'Vérification email échouée'),
        ('sms_verify_send', 'Envoi vérification SMS'),
        ('sms_verify_success', 'Vérification SMS réussie'),
        ('sms_verify_failed', 'Vérification SMS échouée'),
        ('password_change', 'Changement de mot de passe'),
        ('password_reset_request', 'Demande réinitialisation mot de passe'),
        ('password_reset_success', 'Réinitialisation mot de passe réussie'),
        ('profile_update', 'Mise à jour profil'),
        ('account_lock', 'Compte verrouillé'),
        ('account_unlock', 'Compte déverrouillé'),
        ('rate_limit_triggered', 'Limite de tentatives atteinte'),
        ('token_refresh', 'Renouvellement token'),
        ('admin_action', 'Action administrateur'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='security_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_securitylog'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.get_action_display()} - {self.user}"

class LoginAttemptLog(models.Model):
    """Journal spécifique des tentatives de connexion"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(
        max_length=50,
        choices=[
            ('invalid_credentials', 'Identifiants invalides'),
            ('account_inactive', 'Compte inactif'),
            ('account_locked', 'Compte verrouillé'),
            ('email_not_verified', 'Email non vérifié'),
            ('rate_limited', 'Limite dépassée'),
            ('other', 'Autre')
        ],
        null=True,
        blank=True
    )
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_loginattempt'
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]

class TokenUsageLog(models.Model):
    """Journal d'utilisation des tokens"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_type = models.CharField(max_length=20)  # 'verification', 'reset', '2fa'
    action = models.CharField(max_length=50)
    token_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_tokenusage'