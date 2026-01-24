#!/usr/bin/env python
"""
Test pour vérifier que le serializer retourne les réponses
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp, Inscription
from apps.evenements.serializers import InscriptionCreateSerializer

def test_serializer_reponses():
    print("=== TEST SERIALIZER RÉPONSES ===\n")

    # Créer un événement de test
    try:
        evenement = Evenement.objects.create(
            titre='Test Serializer Réponses',
            nombre_places=5,
            statut='ouvert'
        )

        # Créer des champs
        champs = [
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Nom complet',
                type='text',
                ordre=1
            ),
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Âge',
                type='number',
                ordre=2
            ),
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Profession',
                type='select',
                ordre=3,
                options=['Avocat', 'Notaire']
            )
        ]

        print(f"[OK] Evenement et {len(champs)} champs crees")

    except Exception as e:
        print(f"[ERROR] Erreur creation: {e}")
        return

    # Créer une inscription avec réponses
    data = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Serializer",
        "email": "test@example.com",
        "telephone": "0123456789",
        "reponses": [
            {"champ": champs[0].id, "valeur": "John Doe"},
            {"champ": champs[1].id, "valeur": 30},
            {"champ": champs[2].id, "valeur": "Avocat"}
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=data)
        if serializer.is_valid():
            print("[INFO] Serializer valide, creation...")

            # Créer l'inscription
            result = serializer.save()
            print(f"[OK] Inscription creee")

            # Vérifier le résultat retourné
            print(f"[INFO] Type du resultat: {type(result)}")
            print(f"[INFO] Clés du resultat: {result.keys() if isinstance(result, dict) else 'Pas un dict'}")

            if isinstance(result, dict):
                print(f"[INFO] Contenu du resultat:")
                for key, value in result.items():
                    if key == 'reponses':
                        print(f"  {key}: {len(value)} reponses")
                        for i, rep in enumerate(value, 1):
                            print(f"    {i}. {rep}")
                    else:
                        print(f"  {key}: {value}")

                # Vérifier que les réponses sont incluses
                if 'reponses' in result and len(result['reponses']) > 0:
                    print("[SUCCESS] Les reponses sont bien retournees dans la reponse!")
                else:
                    print("[ERROR] Les reponses ne sont pas retournees dans la reponse")
            else:
                print(f"[ERROR] Le serializer retourne un objet {type(result)}, pas un dict")

        else:
            print(f"[ERROR] Erreurs de validation: {serializer.errors}")

    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

    # Nettoyer
    evenement.delete()
    print("\n[OK] Test termine")

if __name__ == '__main__':
    test_serializer_reponses()
