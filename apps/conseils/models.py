# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ConseilsConseildujour(models.Model):
    conseil = models.TextField()
    date = models.DateField(unique=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    public_reference = models.CharField(max_length=50,null=True,blank=True)
    class Meta:
        managed = False
        db_table = 'conseils_conseildujour'
        db_table_comment = "Conseil du jour pour page d'accueil"
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['actif']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        def __str__(self):
            return f"Conseil du {self.date}"
