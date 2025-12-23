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
    user = models.ForeignKey('UtilisateursUser', models.DO_NOTHING)
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
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'core_configuration'
