#!/usr/bin/env python
"""
Debug script pour identifier l'erreur 500 dans la création d'inscriptions
"""
import os
import sys
import django
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from django.test import RequestFactory
from apps.evenements.models import Evenement, EvenementChamp, Inscription, InscriptionReponse
from apps.evenements.serializers import InscriptionCreateSerializer

def test_inscription_creation():
    print("=== DEBUG ERREUR 500 - CRÉATION INSCRIPTION ===\n")

    # 1. Créer un événement de test
    print("1. Création d'un événement de test...")
    try:
        evenement = Evenement.objects.create(
            titre='Debug 500 Error',
            description='Test pour identifier l\'erreur 500',
            nombre_places=5,
            statut='ouvert'
        )
        print(f"[OK] Événement créé: {evenement.id}")
    except Exception as e:
        print(f"[ERROR] Erreur création événement: {e}")
        return

    # 2. Créer des champs dynamiques
    print("\n2. Création des champs dynamiques...")
    try:
        champs = [
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Profession',
                type='text',
                obligatoire=True,
                ordre=1
            ),
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Âge',
                type='number',
                obligatoire=False,
                ordre=2
            ),
            EvenementChamp.objects.create(
                evenement=evenement,
                label='Accepte conditions',
                type='checkbox',
                obligatoire=True,
                ordre=3
            )
        ]
        print(f"[OK] {len(champs)} champs créés")
        for champ in champs:
            print(f"  - {champ.id}: {champ.label} ({champ.type})")
    except Exception as e:
        print(f"[ERROR] Erreur création champs: {e}")
        return

    # 3. Tester les données d'inscription (comme celles envoyées par le frontend)
    print("\n3. Test des données d'inscription...")
    inscription_data = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "User",
        "email": "test@example.com",
        "telephone": "0123456789",
        "reponses": [
            {
                "champ": champs[0].id,  # Profession
                "valeur": "Développeur"
            },
            {
                "champ": champs[1].id,  # Âge
                "valeur": 30
            },
            {
                "champ": champs[2].id,  # Accepte conditions
                "valeur": True
            }
        ]
    }

    print("Données à envoyer:")
    print(json.dumps(inscription_data, indent=2, ensure_ascii=False))

    # 4. Tester la validation du serializer
    print("\n4. Test de validation du serializer...")
    try:
        serializer = InscriptionCreateSerializer(data=inscription_data)
        is_valid = serializer.is_valid()
        print(f"[INFO] Serializer valide: {is_valid}")

        if not is_valid:
            print("Erreurs de validation:")
            for field, errors in serializer.errors.items():
                print(f"  - {field}: {errors}")
            return
        else:
            print("[OK] Validation passée")
    except Exception as e:
        print(f"[ERROR] Erreur lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Tester la création (méthode create du serializer)
    print("\n5. Test de création...")
    try:
        inscription = serializer.save()
        print(f"[OK] Inscription créée: {inscription.id}")
        print(f"[OK] Nom: {inscription.nom} {inscription.prenom}")
        print(f"[OK] Statut: {inscription.statut}")

        # Vérifier les réponses créées
        reponses = inscription.reponses.all()
        print(f"[OK] Nombre de réponses: {reponses.count()}")
        for reponse in reponses:
            valeur = None
            if reponse.valeur_texte:
                valeur = f"'{reponse.valeur_texte}'"
            elif reponse.valeur_nombre is not None:
                valeur = reponse.valeur_nombre
            elif reponse.valeur_bool is not None:
                valeur = reponse.valeur_bool
            print(f"  - {reponse.champ.label}: {valeur}")

    except Exception as e:
        print(f"[ERROR] Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. Vérifier l'événement après création
    print("\n6. Vérification de l'événement après inscription...")
    try:
        evenement.refresh_from_db()
        print(f"[OK] Places restantes: {evenement.nombre_places}")
        print(f"[OK] Statut: {evenement.statut}")
    except Exception as e:
        print(f"[ERROR] Erreur vérification événement: {e}")

    # Nettoyer
    print("\n7. Nettoyage...")
    try:
        evenement.delete()
        print("[OK] Test terminé et nettoyé")
    except Exception as e:
        print(f"[ERROR] Erreur nettoyage: {e}")

def test_erreurs_communes():
    print("\n=== TEST ERREURS COMMUNES ===\n")

    # Test avec champ inexistant
    print("Test 1: Champ inexistant")
    try:
        inscription_data = {
            "evenement": 99999,  # ID qui n'existe pas
            "nom": "Test",
            "prenom": "User",
            "email": "test@example.com",
            "telephone": "0123456789",
            "reponses": []
        }

        serializer = InscriptionCreateSerializer(data=inscription_data)
        is_valid = serializer.is_valid()
        print(f"Champ inexistant - valide: {is_valid}")
        if not is_valid:
            print(f"Erreurs: {serializer.errors}")
    except Exception as e:
        print(f"Exception inattendue: {e}")

    # Test avec valeur incorrecte pour number
    print("\nTest 2: Valeur incorrecte pour champ number")
    try:
        evenement = Evenement.objects.create(
            titre='Test Number',
            nombre_places=5,
            statut='ouvert'
        )
        champ_number = EvenementChamp.objects.create(
            evenement=evenement,
            label='Test Number',
            type='number',
            obligatoire=True,
            ordre=1
        )

        inscription_data = {
            "evenement": evenement.id,
            "nom": "Test",
            "prenom": "User",
            "email": "test@example.com",
            "telephone": "0123456789",
            "reponses": [
                {
                    "champ": champ_number.id,
                    "valeur": "pas_un_nombre"  # Valeur incorrecte
                }
            ]
        }

        serializer = InscriptionCreateSerializer(data=inscription_data)
        is_valid = serializer.is_valid()
        print(f"Valeur incorrecte - valide: {is_valid}")
        if not is_valid:
            print(f"Erreurs: {serializer.errors}")

        evenement.delete()
    except Exception as e:
        print(f"Exception inattendue: {e}")

if __name__ == '__main__':
    try:
        test_inscription_creation()
        test_erreurs_communes()
        print("\n=== DEBUG TERMINÉ ===")
    except Exception as e:
        print(f"ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()
