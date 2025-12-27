# Generated manually for notaire_bf project

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('system', '__first__'),  # Dépend de la première migration de l'app system
        ('utilisateurs', '__first__'),  # Dépend de la première migration de l'app utilisateurs
    ]

    operations = [
        # Création de SystemEmailprofessionnel
        migrations.CreateModel(
            name='SystemEmailprofessionnel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(help_text='Email du domaine professionnel (ex: contact@notairesbf.com)', max_length=254, unique=True, verbose_name='Email professionnel')),
                ('mot_de_passe', models.CharField(help_text='Mot de passe crypté pour l\'accès à la boîte mail', max_length=200, verbose_name='Mot de passe')),
                ('alias_pour', models.EmailField(blank=True, help_text='Si cet email est un alias, indiquer l\'email principal', max_length=254, null=True, verbose_name='Alias pour')),
                ('actif', models.BooleanField(default=True, help_text="Si l'email est actuellement utilisé", verbose_name='Actif')),
                ('description', models.CharField(blank=True, help_text="Usage prévu de cet email (ex: 'Contact général', 'Support technique')", max_length=200, null=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('utilisateur', models.ForeignKey(blank=True, help_text="Utilisateur qui utilise cet email", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails_professionnels', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur associé')),
            ],
            options={
                'verbose_name': 'Email professionnel',
                'verbose_name_plural': 'Emails professionnels',
                'db_table': 'system_emailprofessionnel',
                'ordering': ['email'],
            },
        ),
    ]

