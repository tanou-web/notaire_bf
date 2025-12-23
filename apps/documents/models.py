# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DocumentsDocument(models.Model):
    reference = models.CharField(unique=True, max_length=50)
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    delai_heures = models.IntegerField(db_comment='48h ou 72h uniquement selon cahier des charges')
    actif = models.BooleanField()
    create_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'documents_document'


class DocumentsTextelegal(models.Model):
    type_texte = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True, null=True)
    titre = models.CharField(max_length=200)
    fichier = models.CharField(max_length=200)
    date_publication = models.DateField(blank=True, null=True)
    ordre = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'documents_textelegal'
