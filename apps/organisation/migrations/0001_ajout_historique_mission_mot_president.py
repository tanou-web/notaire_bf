# Generated manually for notaire_bf project

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisation', '__first__'),  # Dépend de la première migration de l'app organisation
    ]

    operations = [
        # Ajout du champ mot_du_president dans OrganisationMembrebureau
        migrations.AddField(
            model_name='organisationmembrebureau',
            name='mot_du_president',
            field=models.TextField(blank=True, help_text="Message du président (visible uniquement si poste='president')", null=True, verbose_name='Mot du Président'),
        ),
        
        # Création de OrganisationHistorique
        migrations.CreateModel(
            name='OrganisationHistorique',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=200, verbose_name='Titre')),
                ('contenu', models.TextField(verbose_name='Contenu')),
                ('date_evenement', models.DateField(blank=True, help_text="Date historique de l'événement", null=True, verbose_name="Date de l'événement")),
                ('ordre', models.IntegerField(default=0, help_text='Ordre chronologique (plus petit = plus ancien)', verbose_name="Ordre d'affichage")),
                ('image', models.ImageField(blank=True, null=True, upload_to='organisation/historique/', verbose_name='Image')),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Événement Historique',
                'verbose_name_plural': 'Historique',
                'db_table': 'organisation_historique',
                'ordering': ['ordre', 'date_evenement', 'created_at'],
            },
        ),
        
        # Création de OrganisationMission
        migrations.CreateModel(
            name='OrganisationMission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=200, verbose_name='Titre')),
                ('description', models.TextField(verbose_name='Description')),
                ('icone', models.CharField(blank=True, help_text="Classe CSS ou nom d'icône (ex: 'fa-users', 'shield')", max_length=50, null=True, verbose_name='Icône')),
                ('ordre', models.IntegerField(default=0, verbose_name="Ordre d'affichage")),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Mission',
                'verbose_name_plural': 'Missions',
                'db_table': 'organisation_mission',
                'ordering': ['ordre', 'titre'],
            },
        ),
    ]

