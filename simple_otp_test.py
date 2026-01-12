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
    print("✅ Django configuré")

    from apps.utilisateurs.models import User, VerificationVerificationtoken
    from apps.utilisateurs.serializers import VerificationTokenGenerator

    # Test de génération et vérification de token
    print("\n=== TEST GÉNÉRATION TOKEN ===")

    # Générer un token
    token = VerificationTokenGenerator.generate_otp(6)
    token_hash = VerificationTokenGenerator.hash_token(token)

    print(f"Token généré: {token}")
    print(f"Hash stocké: {token_hash}")

    # Tester la vérification
    is_valid = VerificationTokenGenerator.verify_token(token_hash, token)
    print(f"Vérification avec bon token: {is_valid}")

    is_invalid = VerificationTokenGenerator.verify_token(token_hash, "999999")
    print(f"Vérification avec mauvais token: {is_invalid}")

    print("\n=== TEST BASE DE DONNÉES ===")

    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='otp_test_user',
        defaults={
            'email': 'otp@test.com',
            'nom': 'OTP',
            'prenom': 'Test',
            'telephone': '+22670000001',
            'is_active': False
        }
    )

    print(f"Utilisateur: {user.username} (ID: {user.id})")

    # Créer un token OTP pour cet utilisateur
    otp_token = VerificationVerificationtoken.objects.create(
        user=user,
        token=token_hash,
        type_token='sms',
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
        data={'purpose': 'test_otp', 'original_token': token}
    )

    print(f"Token OTP créé (ID: {otp_token.id})")
    print(f"Token original pour test: {token}")

    # Tester la recherche du token
    from django.utils import timezone

    found_tokens = VerificationVerificationtoken.objects.filter(
        user=user,
        type_token='sms',
        used=False,
        expires_at__gt=timezone.now()
    )

    print(f"Tokens trouvés: {found_tokens.count()}")

    for vt in found_tokens:
        print(f"Token {vt.id}: {vt.data}")

        # Tester la vérification
        is_token_valid = VerificationTokenGenerator.verify_token(vt.token, token)
        print(f"Vérification du token {vt.id}: {is_token_valid}")

        # Tester avec mauvais token
        is_token_invalid = VerificationTokenGenerator.verify_token(vt.token, "999999")
        print(f"Vérification avec mauvais token: {is_token_invalid}")

    print("\n✅ Tests terminés")

except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()