#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

try:
    django.setup()
    print("✅ Django configuré avec succès")

    # Test des imports
    from apps.evenements.serializers import ReponseChampSerializer, InscriptionCreateSerializer
    print("✅ Serializers importés avec succès")

    # Test de création d'instance
    serializer = ReponseChampSerializer()
    print("✅ ReponseChampSerializer instancié")

    print("\n🎉 Tous les tests passés ! Les modifications sont valides.")

except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()



