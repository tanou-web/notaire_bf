# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class SystemEmailprofessionnel(models.Model):
    email = models.CharField(unique=True, max_length=254)
    mot_de_passe = models.CharField(max_length=200)
    utilisateur = models.ForeignKey('UtilisateursUser', models.DO_NOTHING, blank=True, null=True)
    actif = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'system_emailprofessionnel'
        db_table_comment = '10 emails professionnels selon livrables'
