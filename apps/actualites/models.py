# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ActualitesActualite(models.Model):
    titre = models.CharField(max_length=200)
    slug = models.CharField(unique=True, max_length=200)
    contenu = models.TextField()
    resume = models.CharField(max_length=500, blank=True, null=True)
    categorie = models.CharField(max_length=20)
    image_principale = models.CharField(max_length=200, blank=True, null=True)
    auteur = models.ForeignKey('UtilisateursUser', models.DO_NOTHING, blank=True, null=True)
    date_publication = models.DateTimeField()
    important = models.BooleanField()
    publie = models.BooleanField()
    vue = models.IntegerField()
    featured = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'actualites_actualite'
