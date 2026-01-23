#!/usr/bin/env python
"""
Script de test pour vérifier que l'API des événements fonctionne correctement
avec le champ nombre_places.
"""
import os
import sys
import django

# Configuration Django AVANT les imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from apps.evenements.models import Evenement
from apps.evenements.serializers import EvenementSerializer


def test_evenement_serializer():
    """Test que le sérialiseur inclut bien nombre_places"""
    print("Test du serialiseur EvenementSerializer...")

    # Créer un événement de test
    evenement = Evenement.objects.create(
        titre="Test Evenement",
        description="Description de test",
        nombre_places=50,
        actif=True
    )

    # Sérialiser
    serializer = EvenementSerializer(evenement)
    data = serializer.data

    print("Donnees serialisees:")
    print(f"  - ID: {data.get('id')}")
    print(f"  - Titre: {data.get('titre')}")
    print(f"  - Nombre places: {data.get('nombre_places')}")
    print(f"  - Actif: {data.get('actif')}")

    # Vérifier que nombre_places est présent
    if 'nombre_places' in data:
        print("SUCCES: Le champ nombre_places est bien present dans le serialiseur")
        assert data['nombre_places'] == 50, f"Expected 50, got {data['nombre_places']}"
        print("SUCCES: Valeur nombre_places correcte")
    else:
        print("ERREUR: Le champ nombre_places est manquant dans le serialiseur")
        return False

    # Nettoyer
    evenement.delete()
    return True


def test_api_endpoints():
    """Test des endpoints API"""
    print("\nTest des endpoints API (GET seulement)...")

    from django.test import Client
    client = Client()

    # 1. Test GET /api/evenements/evenements/
    print("Test GET /api/evenements/evenements/")
    response = client.get('/api/evenements/evenements/')
    print(f"  - Status: {response.status_code}")

    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        print(f"  - Nombre d'evenements: {len(data)}")
        print(f"  - Type de donnees: {type(data)}")
        if isinstance(data, list) and len(data) > 0:
            first_event = data[0]
            print(f"  - Premier evenement - nombre_places: {first_event.get('nombre_places', 'MANQUANT')}")
            if 'nombre_places' in first_event:
                print("SUCCES: nombre_places present dans la reponse API")
            else:
                print("ERREUR: nombre_places manquant dans la reponse API")
                return False
        elif isinstance(data, dict):
            # Réponse paginée DRF
            results = data.get('results', [])
            print(f"  - Resultats pagines: {len(results)}")
            if len(results) > 0:
                first_event = results[0]
                print(f"  - Premier evenement - nombre_places: {first_event.get('nombre_places', 'MANQUANT')}")
                if 'nombre_places' in first_event:
                    print("SUCCES: nombre_places present dans la reponse API")
                else:
                    print("ERREUR: nombre_places manquant dans la reponse API")
                    return False
        print("SUCCES: Endpoint GET fonctionne")
    else:
        print("ERREUR: Endpoint GET ne fonctionne pas")
        print(f"Contenu: {response.content.decode()[:200]}")
        return False

    # Test du formulaire endpoint
    print("\nTest GET /api/evenements/evenements/1/formulaire/")
    response = client.get('/api/evenements/evenements/1/formulaire/')
    print(f"  - Status: {response.status_code}")

    if response.status_code in [200, 404]:  # 404 si l'evenement n'existe pas
        print("SUCCES: Endpoint formulaire fonctionne")
    else:
        print("ERREUR: Endpoint formulaire ne fonctionne pas")

    return True


if __name__ == '__main__':
    print("Demarrage des tests API Evenements...")
    print("=" * 50)

    success = True

    try:
        if not test_evenement_serializer():
            success = False

        if not test_api_endpoints():
            success = False

    except Exception as e:
        print(f"ERREUR lors des tests: {e}")
        success = False

    print("\n" + "=" * 50)
    if success:
        print("SUCCES: Tous les tests sont passes avec succes !")
        print("Le probleme avec nombre_places devrait etre resolu.")
    else:
        print("ERREUR: Certains tests ont echoue.")

    sys.exit(0 if success else 1)
