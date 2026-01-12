# Generated manually for adding 'used' field to VerificationVerificationtoken

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificationverificationtoken',
            name='used',
            field=models.BooleanField(default=False, verbose_name='Utilisé'),
        ),
    ]