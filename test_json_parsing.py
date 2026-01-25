#!/usr/bin/env python
"""
Test du parsing JSON dans FormData
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.serializers import InscriptionCreateSerializer

def test_json_parsing():
    print("=== TEST PARSING JSON DANS FORMDATA ===\n")

    # Test 1: Données normales (dict Python)
    print("1. Test avec données Python normales:")
    data_python = {
        'evenement': 1,
        'nom': 'Test',
        'prenom': 'User',
        'email': 'test@example.com',
        'telephone': '0123456789',
        'reponses': [
            {'champ': 1, 'valeur': 'Texte'},
            {'champ': 2, 'valeur': 30}
        ]
    }

    serializer1 = InscriptionCreateSerializer(data=data_python)
    is_valid1 = serializer1.is_valid()
    print(f"Validation: {is_valid1}")
    if not is_valid1:
        print(f"Erreurs: {serializer1.errors}")
    else:
        print("✅ Données Python acceptées")
    print()

    # Test 2: Simulation FormData avec string JSON
    print("2. Test avec string JSON (comme FormData):")
    data_formdata = {
        'evenement': '1',  # String comme dans FormData
        'nom': 'Test',
        'prenom': 'User',
        'email': 'test@example.com',
        'telephone': '0123456789',
        'reponses': '[{"champ": 1, "valeur": "Texte"}, {"champ": 2, "valeur": 30}]'  # String JSON
    }

    serializer2 = InscriptionCreateSerializer(data=data_formdata)
    is_valid2 = serializer2.is_valid()
    print(f"Validation: {is_valid2}")
    if not is_valid2:
        print(f"Erreurs: {serializer2.errors}")
    else:
        print("✅ String JSON parsée correctement")
        print(f"Données internes: {serializer2.validated_data}")
    print()

    # Test 3: JSON invalide
    print("3. Test avec JSON invalide:")
    data_invalid = {
        'evenement': '1',
        'nom': 'Test',
        'prenom': 'User',
        'email': 'test@example.com',
        'telephone': '0123456789',
        'reponses': '{"champ": 1, "valeur": "Texte"'  # JSON invalide (manque })
    }

    serializer3 = InscriptionCreateSerializer(data=data_invalid)
    is_valid3 = serializer3.is_valid()
    print(f"Validation: {is_valid3}")
    if not is_valid3:
        print(f"Erreurs: {serializer3.errors}")
        if 'reponses' in str(serializer3.errors):
            print("✅ Erreur JSON détectée correctement")
    print()

    print("=== TEST TERMINÉ ===")

if __name__ == '__main__':
    test_json_parsing()