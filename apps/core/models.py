# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthRole(models.Model):
    nom = models.CharField(unique=True, max_length=50)
    permissions = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_role'


class AuthUserrole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING)
    role = models.ForeignKey(AuthRole, models.DO_NOTHING)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_userrole'
        unique_together = (('user', 'role'),)


class CoreConfiguration(models.Model):
    cle = models.CharField(unique=True, max_length=100)
    valeur = models.JSONField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'core_configuration'


class CorePage(models.Model):
    """Pages CMS génériques pour gestion de contenu dynamique"""
    
    titre = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(
        unique=True,
        max_length=200,
        verbose_name="Slug",
        help_text="URL de la page (ex: 'a-propos', 'presentation')"
    )
    
    contenu = models.TextField(
        verbose_name="Contenu",
        help_text="Contenu HTML de la page"
    )
    
    resume = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name="Résumé",
        help_text="Résumé court pour les aperçus"
    )
    
    template = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='page_standard.html',
        verbose_name="Template",
        help_text="Template à utiliser pour le rendu"
    )
    
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Meta Title",
        help_text="Titre SEO"
    )
    
    meta_description = models.TextField(
        blank=True,
        null=True,
        max_length=300,
        verbose_name="Meta Description",
        help_text="Description SEO"
    )
    
    image_principale = models.ImageField(
        upload_to='pages/',
        blank=True,
        null=True,
        verbose_name="Image principale"
    )
    
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    publie = models.BooleanField(
        default=False,
        verbose_name="Publié",
        help_text="Si la page est visible publiquement"
    )
    
    date_publication = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de publication"
    )
    
    auteur = models.ForeignKey(
        'utilisateurs.UtilisateursUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pages_creees',
        verbose_name="Auteur"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_page'
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
        ordering = ['ordre', 'titre']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['publie', 'date_publication']),
        ]

    def __str__(self):
        return f"{self.titre} ({'Publié' if self.publie else 'Brouillon'})"
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        # Auto-définir la date de publication si publié et date non définie
        if self.publie and not self.date_publication:
            self.date_publication = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def url(self):
        """Retourne l'URL de la page"""
        return f"/pages/{self.slug}/"
