#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

try:
    django.setup()
    print("✅ Django configuré avec succès")

    # Test 1: Vérifier la structure de la base de données
    print("\n=== TEST 1: STRUCTURE BASE DE DONNÉES ===")

    from django.db import connection
    with connection.cursor() as cursor:
        # Vérifier si la table verification_verificationtoken existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='verification_verificationtoken';
        """)
        table_exists = cursor.fetchone()
        print(f"Table verification_verificationtoken existe: {table_exists is not None}")

        if table_exists:
            # Vérifier les colonnes de la table
            cursor.execute("PRAGMA table_info(verification_verificationtoken);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"Colonnes de la table: {column_names}")

            # Vérifier si la colonne 'used' existe
            has_used_column = 'used' in column_names
            print(f"Colonne 'used' existe: {has_used_column}")

    # Test 2: Tester les imports
    print("\n=== TEST 2: IMPORTS ===")

    try:
        from apps.utilisateurs.models import User, VerificationVerificationtoken
        from apps.utilisateurs.views import LoginView, AdminCreateView
        from apps.utilisateurs.serializers import UserSerializer, AdminCreateSerializer
        print("✅ Tous les imports réussis")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")

    # Test 3: Tester la création d'un utilisateur
    print("\n=== TEST 3: CRÉATION UTILISATEUR ===")

    try:
        from apps.utilisateurs.models import User

        # Vérifier s'il y a des utilisateurs existants
        user_count = User.objects.count()
        print(f"Nombre d'utilisateurs existants: {user_count}")

        # Tester la création d'un token de vérification
        from apps.utilisateurs.models import VerificationVerificationtoken
        from django.utils import timezone

        token_count = VerificationVerificationtoken.objects.count()
        print(f"Nombre de tokens de vérification: {token_count}")

        # Tester la création d'un token
        test_user, created = User.objects.get_or_create(
            username='diagnostic_test',
            defaults={
                'email': 'diagnostic@test.com',
                'nom': 'Diagnostic',
                'prenom': 'Test',
                'is_active': False
            }
        )

        # Créer un token de test
        test_token = VerificationVerificationtoken.objects.create(
            user=test_user,
            token='test_hash',
            type_token='sms',
            used=False,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
            data={'test': True}
        )

        print(f"✅ Token de test créé avec ID: {test_token.id}")

        # Nettoyer
        test_token.delete()
        if created:
            test_user.delete()

        print("✅ Test de création réussi")

    except Exception as e:
        print(f"❌ Erreur lors de la création: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 4: Tester les URLs
    print("\n=== TEST 4: URLs ===")

    try:
        from django.urls import reverse
        # Tester les URLs principales
        login_url = reverse('login')
        print(f"URL login: {login_url}")

        # Tester les URLs des viewsets
        from django.test import Client
        client = Client()

        # Test basique de l'URL login
        response = client.get('/api/auth/login/')
        print(f"GET /api/auth/login/ - Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Erreur URLs: {str(e)}")

    print("\n=== DIAGNOSTIC TERMINÉ ===")

except Exception as e:
    print(f"❌ Erreur générale: {str(e)}")
    import traceback
    traceback.print_exc()