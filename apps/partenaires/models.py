from django.db import models

class PartenairesPartenaire(models.Model):
    nom = models.CharField(max_length=200)
    type_partenaire = models.CharField(max_length=20)
    logo = models.ImageField(upload_to='partenaires/logos/', blank=True, null=True)
    url = models.URLField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partenaires_partenaire'
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom
