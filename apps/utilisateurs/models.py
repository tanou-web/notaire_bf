from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Modèle utilisateur personnalisé pour l'Ordre des Notaires"""
    
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email_verifie = models.BooleanField(default=False, verbose_name="Email vérifié")
    telephone_verifie = models.BooleanField(default=False, verbose_name="Téléphone vérifié")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        db_table = 'utilisateurs_user'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.username})"

    def get_full_name(self):
        return f"{self.nom} {self.prenom}".strip()


class VerificationVerificationtoken(models.Model):
    """Modèle pour les tokens de vérification (email, téléphone, mot de passe)"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens',
        verbose_name="Utilisateur"
    )
    token = models.CharField(max_length=100, verbose_name="Token")
    type_token = models.CharField(
        max_length=30,
        verbose_name="Type de token",
        choices=[
            ('email', 'Email'),
            ('telephone', 'Téléphone'),
            ('password_reset', 'Réinitialisation mot de passe'),
        ]
    )
    expires_at = models.DateTimeField(verbose_name="Expire le")
    data = models.JSONField(default=dict, blank=True, verbose_name="Données supplémentaires")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        db_table = 'verification_verificationtoken'
        verbose_name = "Token de vérification"
        verbose_name_plural = "Tokens de vérification"
        ordering = ['-create_at']

    def __str__(self):
        return f"{self.user.username} - {self.type_token} - {self.token[:10]}..."

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


# Alias pour compatibilité avec le code existant
UtilisateursUser = User