#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

import requests
import json
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_create_admin():
    """Test direct de l'API de création d'admin"""
    print("=== TEST API CREATE ADMIN ===")

    # Créer un client de test
    client = Client()

    # Créer d'abord un superuser pour les tests
    try:
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            superuser = User.objects.create_superuser(
                username='test_superuser',
                email='super@test.com',
                password='Test123!@#',
                nom='Super',
                prenom='User'
            )
            print(f"✅ Superuser créé: {superuser.username}")
        else:
            print(f"✅ Superuser existant: {superuser.username}")

        # Se connecter
        login_response = client.post('/api/auth/login/', {
            'email': 'super@test.com',
            'password': 'Test123!@#'
        }, content_type='application/json')

        print(f"Login status: {login_response.status_code}")
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('access')
            print(f"✅ Token obtenu: {token[:20]}...")

            # Tester la création d'admin
            headers = {
                'HTTP_AUTHORIZATION': f'Bearer {token}',
                'content_type': 'application/json'
            }

            admin_data = {
                'username': 'test_admin_123',
                'email': 'test.admin@example.com',
                'password': 'Test123!@#',
                'password_confirmation': 'Test123!@#',
                'nom': 'Test',
                'prenom': 'Admin',
                'telephone': '+22670000001',
                'is_staff': True,
                'is_superuser': True
            }

            print(f"📤 Envoi données: {admin_data}")

            response = client.post(
                '/api/auth/create-admin/',
                data=json.dumps(admin_data),
                **headers
            )

            print(f"📥 Réponse status: {response.status_code}")
            print(f"📥 Headers: {dict(response.headers)}")

            try:
                response_data = response.json()
                print(f"📥 Réponse JSON: {response_data}")
            except:
                print(f"📥 Réponse texte: {response.content[:500]}")

        else:
            print(f"❌ Échec login: {login_response.content}")

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_create_admin()