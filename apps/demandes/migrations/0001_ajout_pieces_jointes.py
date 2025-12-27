# Generated manually for notaire_bf project

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demandes', '__first__'),  # Dépend de la première migration de l'app demandes
    ]

    operations = [
        # Création de DemandesPieceJointe
        migrations.CreateModel(
            name='DemandesPieceJointe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_piece', models.CharField(choices=[('cnib', 'CNIB (Carte Nationale d\'Identité Burkinabé)'), ('passeport', 'Passeport'), ('document_identite', 'Autre document d\'identité'), ('document_legal', 'Document légal'), ('autre', 'Autre document')], max_length=30, verbose_name='Type de pièce')),
                ('fichier', models.FileField(help_text='Format accepté: PDF, JPG, PNG (max 10MB)', upload_to='demandes/pieces_jointes/%Y/%m/', verbose_name='Fichier')),
                ('nom_original', models.CharField(blank=True, max_length=255, verbose_name='Nom original du fichier')),
                ('taille_fichier', models.PositiveIntegerField(blank=True, null=True, verbose_name='Taille du fichier (octets)')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('demande', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pieces_jointes', to='demandes.demandesdemande', verbose_name='Demande')),
            ],
            options={
                'verbose_name': 'Pièce jointe',
                'verbose_name_plural': 'Pièces jointes',
                'db_table': 'demandes_piecejointe',
                'ordering': ['-created_at'],
            },
        ),
    ]

