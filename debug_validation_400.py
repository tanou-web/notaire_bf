#!/usr/bin/env python
"""
Debug de l'erreur 400 pour comprendre quelle validation échoue
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp
from apps.evenements.serializers import InscriptionCreateSerializer

def debug_validation_400():
    print("=== DEBUG ERREUR 400 - VALIDATION ===")

    # Simuler les données exactes envoyées par le frontend
    print("\n📦 Données reçues du frontend :")
    frontend_data = {
        'evenement': '8',  # String comme dans FormData
        'nom': 'Bngo',
        'prenom': 'Dems',
        'email': 'clovdesign14@gmail.com',
        'telephone': '53169736',
        'reponses': '[{"champ":8,"valeur":"Dems Bngo"},{"champ":9,"valeur":74},{"champ":10,"valeur":"Avocat"},{"champ":11,"valeur":"Dems"},{"champ":12,"valeur":"14/11/2016"},{"champ":13,"valeur":true},{"champ":39,"valeur":"0540-tutoriel-sur-laravel.pdf"}]'  # JSON string
    }

    print("Données brutes:")
    for key, value in frontend_data.items():
        print(f"  {key}: {value}")

    # Tester la validation
    print("\n🔍 Test de validation:")
    serializer = InscriptionCreateSerializer(data=frontend_data)

    is_valid = serializer.is_valid()
    print(f"Validation: {is_valid}")

    if not is_valid:
        print("\n❌ Erreurs de validation:")
        for field, errors in serializer.errors.items():
            print(f"  {field}:")
            for error in errors:
                print(f"    - {error}")
    else:
        print("✅ Validation réussie")

    # Vérifier l'événement 8
    print("\n🏛️ Vérification de l'événement 8:")
    try:
        from apps.evenements.models import Evenement
        event = Evenement.objects.get(id=8)
        print(f"  Événement trouvé: {event.titre}")
        print(f"  Statut: {event.statut}")
        print(f"  Actif: {event.actif}")
        print(f"  Places: {event.nombre_places}")

        # Vérifier les champs
        champs = event.champs.filter(actif=True)
        print(f"  Nombre de champs actifs: {champs.count()}")

        print("  Détails des champs:")
        for champ in champs:
            print(f"    ID {champ.id}: {champ.label} ({champ.type}) - obligatoire: {champ.obligatoire}")
            if champ.type == 'select' and champ.options:
                print(f"      Options: {champ.options}")

    except Evenement.DoesNotExist:
        print("  ❌ Événement 8 n'existe pas!")
    except Exception as e:
        print(f"  ❌ Erreur événement: {e}")

    # Vérifier les champs mentionnés dans les réponses
    print("\n📋 Vérification des champs utilisés:")
    champ_ids = [8, 9, 10, 11, 12, 13, 39]

    for champ_id in champ_ids:
        try:
            champ = EvenementChamp.objects.get(id=champ_id, evenement_id=8, actif=True)
            print(f"  ✅ Champ {champ_id}: {champ.label} ({champ.type}) - OK")
        except EvenementChamp.DoesNotExist:
            print(f"  ❌ Champ {champ_id}: N'existe pas ou inactif")
        except Exception as e:
            print(f"  ❌ Erreur champ {champ_id}: {e}")

    print("\n🎯 ANALYSE DE L'ERREUR 400:")
    print("L'erreur 400 indique un problème de validation des données.")
    print("Vérifiez:")
    print("1. L'événement 8 existe et est actif")
    print("2. Tous les champs (8,9,10,11,12,13,39) existent et sont actifs")
    print("3. Les valeurs correspondent aux types attendus")
    print("4. Les champs obligatoires ont des valeurs")
    print("5. Pour les selects, les valeurs sont dans les options")

if __name__ == '__main__':
    debug_validation_400()






