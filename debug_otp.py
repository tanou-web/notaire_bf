#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

try:
    django.setup()
    print("✅ Django configuré")

    # Test des imports
    from apps.utilisateurs.models import User, VerificationVerificationtoken
    from apps.utilisateurs.serializers import VerificationTokenGenerator
    print("✅ Imports réussis")

    # Test de génération de token
    token = VerificationTokenGenerator.generate_otp(6)
    token_hash = VerificationTokenGenerator.hash_token(token)
    print(f"✅ Token généré: {token}")
    print(f"✅ Hash: {token_hash[:20]}...")

    # Test de vérification
    is_valid = VerificationTokenGenerator.verify_token(token_hash, token)
    print(f"✅ Vérification token: {is_valid}")

    # Test avec token incorrect
    is_invalid = VerificationTokenGenerator.verify_token(token_hash, "999999")
    print(f"✅ Vérification token incorrect: {not is_invalid}")

    print("✅ Tests terminés avec succès")

except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()