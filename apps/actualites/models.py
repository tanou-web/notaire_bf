from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import F
from django.conf import settings


class ActualitesActualite(models.Model):
    CATEGORIE_CHOICES = [
        ('profession', 'Profession'),
        ('juridique', 'Juridique'),
        ('formation', 'Formation'),
        ('evenement', 'Événement'),
        ('autre', 'Autre'),
    ]

    titre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    contenu = models.TextField()
    resume = models.CharField(max_length=500, blank=True, null=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIE_CHOICES)

    image_principale = models.ImageField(
        upload_to='actualites/photos/',
        blank=True,
        null=True,
        verbose_name="Photo de l'actualité"
    )

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='actualites',
        verbose_name="Auteur"
    )

    date_publication = models.DateTimeField(blank=True, null=True)
    important = models.BooleanField(default=False)
    publie = models.BooleanField(default=False)
    vue = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)

    class Meta:
        db_table = 'actualites_actualite'
        ordering = ['-date_publication', '-created_at']

    def __str__(self):
        return self.titre

    def clean(self):
        valid_categories = [choice[0] for choice in self.CATEGORIE_CHOICES]
        if self.categorie not in valid_categories:
            raise ValidationError(
                f"Catégorie invalide. Doit être parmi: {', '.join(valid_categories)}"
            )

        if self.publie and self.date_publication and self.date_publication > timezone.now():
            raise ValidationError(
                "Une actualité publiée ne peut pas avoir une date de publication dans le futur"
            )


    def save(self, *args, **kwargs):
        now = timezone.now()

        if not self.slug:
            self.slug = slugify(self.titre)

        if not self.pk:
            original_slug = self.slug
            counter = 1
            while ActualitesActualite.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}--{counter}'
                counter += 1
            self.created_at = now

        if self.publie and not self.date_publication:
            self.date_publication = now

        self.updated_at = now
        super().save(*args, **kwargs)

    def incrementer_vues(self):
        ActualitesActualite.objects.filter(pk=self.pk).update(vue=F('vue') + 1)

    @property
    def est_publiee(self):
        return (
            self.publie
            and self.date_publication
            and self.date_publication <= timezone.now()
        )

    @property
    def categorie_display(self):
        return dict(self.CATEGORIE_CHOICES).get(self.categorie, self.categorie)

    @property
    def resume_auto(self):
        if self.resume:
            return self.resume
        if not self.contenu:
            return ""
        return self.contenu[:150] + "..." if len(self.contenu) > 150 else self.contenu
