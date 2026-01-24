#!/usr/bin/env python
"""
Test de la correction du format de date dans les inscriptions
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp, Inscription
from apps.evenements.serializers import InscriptionCreateSerializer

def test_date_formats():
    print("=== TEST FORMAT DE DATE ===\n")

    # Créer un événement de test
    try:
        evenement = Evenement.objects.create(
            titre='Test Date Format',
            description='Test des formats de date',
            nombre_places=5,
            statut='ouvert'
        )

        # Créer un champ de type date
        champ_date = EvenementChamp.objects.create(
            evenement=evenement,
            label='Date de naissance',
            type='date',
            obligatoire=True,
            ordre=1
        )

        print(f"[OK] Evenement cree: {evenement.id}")
        print(f"[OK] Champ date cree: {champ_date.id}")

    except Exception as e:
        print(f"[ERROR] Erreur creation: {e}")
        return

    # Test 1: Format ISO (AAAA-MM-JJ)
    print("\n1. Test format ISO (AAAA-MM-JJ): 1990-05-15")
    test_data_iso = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "ISO",
        "email": "iso@example.com",
        "telephone": "0123456789",
        "reponses": [
            {
                "champ": champ_date.id,
                "valeur": "1990-05-15"
            }
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=test_data_iso)
        if serializer.is_valid():
            inscription = serializer.save()
            print(f"[OK] Inscription ISO creee: {inscription.id}")

            # Vérifier la date sauvegardée
            reponse = inscription.reponses.first()
            if reponse and reponse.valeur_date:
                print(f"[OK] Date sauvegardee: {reponse.valeur_date}")
            else:
                print("[ERROR] Date non sauvegardee")
        else:
            print(f"[ERROR] Erreurs validation: {serializer.errors}")

    except Exception as e:
        print(f"[ERROR] Exception: {e}")

    # Test 2: Format français (JJ/MM/AAAA)
    print("\n2. Test format francais (JJ/MM/AAAA): 15/05/1990")
    test_data_fr = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Francais",
        "email": "francais@example.com",
        "telephone": "0123456789",
        "reponses": [
            {
                "champ": champ_date.id,
                "valeur": "15/05/1990"
            }
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=test_data_fr)
        if serializer.is_valid():
            inscription = serializer.save()
            print(f"[OK] Inscription francaise creee: {inscription.id}")

            # Vérifier la date sauvegardée
            reponse = inscription.reponses.first()
            if reponse and reponse.valeur_date:
                print(f"[OK] Date sauvegardee: {reponse.valeur_date}")
            else:
                print("[ERROR] Date non sauvegardee")
        else:
            print(f"[ERROR] Erreurs validation: {serializer.errors}")

    except Exception as e:
        print(f"[ERROR] Exception: {e}")

    # Test 3: Format invalide
    print("\n3. Test format invalide: 15-05-1990")
    test_data_invalid = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Invalide",
        "email": "invalide@example.com",
        "telephone": "0123456789",
        "reponses": [
            {
                "champ": champ_date.id,
                "valeur": "15-05-1990"  # Format invalide
            }
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=test_data_invalid)
        if serializer.is_valid():
            print("[ERROR] Format invalide accepte - BUG!")
        else:
            print(f"[OK] Format invalide rejete: {serializer.errors}")

    except Exception as e:
        print(f"[OK] Exception attendue pour format invalide: {e}")

    # Nettoyer
    print("\n4. Nettoyage...")
    evenement.delete()
    print("[OK] Test termine")

if __name__ == '__main__':
    test_date_formats()
