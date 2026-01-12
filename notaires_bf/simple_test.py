#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
sys.path.append(r'C:\Users\DELL\Desktop\notaire_bf (2)')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

try:
    django.setup()
    print("✅ Django configuré avec succès")

    # Test des imports
    from apps.utilisateurs.models import User
    from apps.utilisateurs.serializers import AdminCreateSerializer
    print("✅ Imports réussis")

    # Test de base du serializer
    data = {
        'username': 'test_admin',
        'email': 'test@example.com',
        'password': 'Test123!@#',
        'password_confirmation': 'Test123!@#',
        'nom': 'Test',
        'prenom': 'Admin',
        'telephone': '+22670000001'
    }

    serializer = AdminCreateSerializer(data=data)
    is_valid = serializer.is_valid()
    print(f"✅ Serializer valide: {is_valid}")

    if not is_valid:
        print(f"❌ Erreurs: {serializer.errors}")

    print("✅ Tests terminés avec succès")

except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()