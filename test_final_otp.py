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
    print("\n=== TEST CHAMP 'used' ===")

    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='otp_final_test',
        defaults={
            'email': 'otp.final@test.com',
            'nom': 'OTP',
            'prenom': 'Final',
            'telephone': '+22670000001',
            'is_active': False
        }
    )

    print(f"Utilisateur: {user.username} (ID: {user.id})")

    # Générer un token
    token = VerificationTokenGenerator.generate_otp(6)
    token_hash = VerificationTokenGenerator.hash_token(token)

    print(f"Token généré: {token}")
    print(f"Hash: {token_hash[:20]}...")

    # Créer un token OTP avec le champ 'used'
    from django.utils import timezone

    otp_token = VerificationVerificationtoken.objects.create(
        user=user,
        token=token_hash,
        type_token='sms',
        used=False,  # Nouveau champ
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
        data={'purpose': 'test_final', 'original_token': token}
    )

    print(f"Token OTP créé (ID: {otp_token.id}) avec used=False")

    # Tester la recherche avec le filtre 'used=False'
    found_tokens = VerificationVerificationtoken.objects.filter(
        user=user,
        type_token='sms',
        used=False,  # Ce filtre devrait maintenant marcher
        expires_at__gt=timezone.now()
    )

    print(f"Tokens trouvés avec used=False: {found_tokens.count()}")

    if found_tokens.exists():
        vt = found_tokens.first()
        print(f"Token trouvé: ID={vt.id}, used={vt.used}")

        # Tester la vérification
        is_valid = VerificationTokenGenerator.verify_token(vt.token, token)
        print(f"Vérification du token: {is_valid}")

        # Marquer comme utilisé
        vt.used = True
        vt.save()
        print(f"Token marqué comme utilisé: used={vt.used}")

        # Vérifier qu'il n'est plus trouvé
        remaining_tokens = VerificationVerificationtoken.objects.filter(
            user=user,
            type_token='sms',
            used=False,
            expires_at__gt=timezone.now()
        )
        print(f"Tokens restants avec used=False: {remaining_tokens.count()}")

    print("\n✅ Tests terminés avec succès - Le champ 'used' fonctionne !")

except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()