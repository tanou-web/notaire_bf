# Generated manually for notaire_bf project

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contact', '__first__'),  # Dépend de la première migration de l'app contact
    ]

    operations = [
        # Ajout des champs latitude et longitude dans ContactInformations
        migrations.AddField(
            model_name='contactinformations',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Pour affichage sur carte (Google Maps)', max_digits=9, null=True, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='contactinformations',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Pour affichage sur carte (Google Maps)', max_digits=9, null=True, verbose_name='Longitude'),
        ),
    ]

