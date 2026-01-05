# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DocumentsDocument(models.Model):
    DELAI_CHOICES = (
        (48, '48 heures'),
        (72, '72 heures'),
    )

    id = models.AutoField(primary_key=True)
    reference = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    delai_heures = models.IntegerField(choices=DELAI_CHOICES)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fichier = models.FileField(
    upload_to='documents/%Y/%m/',
    blank=True,
    null=True,
    verbose_name="Fichier PDF"
    )


    class Meta:
        managed = True
        db_table = 'documents_document'

    def __str__(self):
        return f"{self.reference} - {self.nom}"


class DocumentsTextelegal(models.Model):
    TYPE_CHOICES = (
        ('loi', 'Loi'),
        ('decret', 'Décret'),
        ('arrete', 'Arrêté'),
        ('reglement_interieur', 'Règlement intérieur'),
    )

    id = models.AutoField(primary_key=True)
    type_texte = models.CharField(max_length=50, choices=TYPE_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)
    titre = models.CharField(max_length=200)
    fichier = models.FileField(
        upload_to='texte_legaux/%Y/%m/',
        blank=True,
        null=True
    )
    date_publication = models.DateField(blank=True, null=True)
    ordre = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'documents_textelegal'

    def __str__(self):
        return self.titre
