import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notaires_bf.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    # Vérifie si un superuser existe déjà
    if User.objects.filter(is_superuser=True).exists():
        print("Un superuser existe déjà !")
    else:
        user = User.objects.create_superuser(
            username="admin",
            email="tanouahmadou043@gmail.com",
            password="admin1234"
        )
        print(f"Superuser créé: {user.username} ({user.email})")
except Exception as e:
    print("Erreur:", e)
