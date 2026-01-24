#!/usr/bin/env python
"""
Test de la correction du serializer pour éviter l'erreur 500
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp
from apps.evenements.serializers import InscriptionCreateSerializer

def test_serializer_fix():
    print("=== TEST CORRECTION SERIALIZER ===")

    # Créer un événement de test
    try:
        evenement = Evenement.objects.create(
            titre='Test Serializer Fix',
            nombre_places=5,
            statut='ouvert'
        )

        # Créer des champs
        champs = [
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Nom',
                type='text',
                ordre=1
            ),
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Age',
                type='number',
                ordre=2
            )
        ]

        print(f"[OK] Evenement et {len(champs)} champs crees")

    except Exception as e:
        print(f"[ERROR] Erreur creation: {e}")
        return

    # Créer une inscription
    data = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Serializer",
        "email": "test@example.com",
        "telephone": "0123456789",
        "reponses": [
            {"champ": champs[0].id, "valeur": "John Doe"},
            {"champ": champs[1].id, "valeur": 30}
        ]
    }

    try:
        print("[INFO] Test creation avec le nouveau serializer...")

        serializer = InscriptionCreateSerializer(data=data)
        if serializer.is_valid():
            result = serializer.save()
            print("[OK] Inscription creee")

            # Vérifier le format de la réponse
            print("[INFO] Verification du format de reponse:")
            print(f"  - Type: {type(result)}")
            print(f"  - Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            if isinstance(result, dict):
                print("  - Contenu:")
                for key, value in result.items():
                    if key == 'reponses':
                        print(f"    {key}: {len(value)} reponses")
                        for i, rep in enumerate(value[:2], 1):  # Afficher seulement les 2 premiers
                            print(f"      {i}. {rep}")
                    else:
                        print(f"    {key}: {value}")

                # Vérifications
                assert 'id' in result, "ID manquant"
                assert 'reponses' in result, "Reponses manquantes"
                assert len(result['reponses']) == 2, f"Mauvais nombre de reponses: {len(result['reponses'])}"

                print("[SUCCESS] Format de reponse correct!")
            else:
                print("[ERROR] La reponse n'est pas un dictionnaire")

        else:
            print(f"[ERROR] Erreurs validation: {serializer.errors}")

    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

    # Nettoyer
    evenement.delete()
    print("[OK] Test termine")

if __name__ == '__main__':
    test_serializer_fix()
