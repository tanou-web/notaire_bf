# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ContactInformations(models.Model):
    TYPE_CHOICES = [
        ('adresse', 'Adresse'),
        ('telephone', 'Téléphone'),
        ('email', 'Email'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    valeur = models.CharField(max_length=500)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude",
        help_text="Pour affichage sur carte (Google Maps)"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude",
        help_text="Pour affichage sur carte (Google Maps)"
    )
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'contact_informations'
        verbose_name = 'Information de Contact'
        verbose_name_plural = 'Informations de Contact'
        ordering = ['ordre', 'type']

    def __str__(self):
        return f"{self.get_type_display()}: {self.valeur}"


class ContactMessage(models.Model):
    """Managed model to store contact form submissions."""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'contact_messages'

    def __str__(self):
        return f"ContactMessage({self.email} - {self.subject})"
