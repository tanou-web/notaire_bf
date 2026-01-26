from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator

# models.py
class Evenement(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('ouvert', 'Ouvert'),
        ('complet', 'Complet'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]

    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')  # <- ajouté
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    nombre_places = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.titre   

class EvenementChamp(models.Model):
    TYPE_CHOICES = [
        ('text', 'Texte'),
        ('textarea', 'Zone de texte'),
        ('number', 'Nombre'),
        ('date', 'Date'),
        ('checkbox', 'Case à cocher'),
        ('select', 'Liste déroulante'),
        ('file', 'Fichier'),
    ]

    evenement = models.ForeignKey(
        Evenement,
        on_delete=models.CASCADE,
        related_name='champs'
    )
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    obligatoire = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=0)
    options = models.JSONField(blank=True, null=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label} ({self.evenement})"

class Inscription(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
        ('annulee', 'Annulée'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')  # <- ajouté
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"  

class InscriptionReponse(models.Model):
    inscription = models.ForeignKey(
        Inscription,
        on_delete=models.CASCADE,
        related_name='reponses'
    )
    champ = models.ForeignKey(EvenementChamp, on_delete=models.CASCADE)

    valeur_texte = models.TextField(blank=True, null=True)
    valeur_nombre = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valeur_date = models.DateField(blank=True, null=True)
    
    # CORRIGE LE BOOLEANFIELD :
    valeur_bool = models.BooleanField(default=None, null=True, blank=True)
    
    # AJOUTE DES VALIDATEURS POUR LES FICHIERS :
    valeur_fichier = models.FileField(
        upload_to='evenements/reponses/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            )
        ]
    )

    def _str_(self):
        return f"{self.inscription} - {self.champ.label}"
