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

    from django.test import Client
    from apps.utilisateurs.models import User, VerificationVerificationtoken
    from apps.utilisateurs.serializers import VerificationTokenGenerator

    # Créer un client de test
    client = Client()

    # Créer un superuser pour les tests
    superuser, created = User.objects.get_or_create(
        username='debug_superuser',
        defaults={
            'email': 'debug@super.com',
            'nom': 'Debug',
            'prenom': 'Super',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )

    if created:
        superuser.set_password('Debug123!@#')
        superuser.save()
        print("✅ Superuser créé")

    # Se connecter
    login_response = client.post('/api/auth/login/', {
        'email': 'debug@super.com',
        'password': 'Debug123!@#'
    }, content_type='application/json')

    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('access')
        print(f"✅ Token obtenu: {token[:20]}...")

        # Créer un nouvel admin
        admin_data = {
            'username': 'debug_admin_123',
            'email': 'debug.admin@example.com',
            'password': 'Debug123!@#',
            'password_confirmation': 'Debug123!@#',
            'nom': 'Debug',
            'prenom': 'Admin',
            'telephone': '+22670000001'
        }

        create_response = client.post(
            '/api/auth/create-admin/',
            data=json.dumps(admin_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        print(f"📤 Création admin - Status: {create_response.status_code}")
        if create_response.status_code == 201:
            create_data = create_response.json()
            user_id = create_data['user_id']
            print(f"✅ Admin créé avec ID: {user_id}")

            # Vérifier que le token OTP a été créé
            try:
                user = User.objects.get(id=user_id)
                tokens = VerificationVerificationtoken.objects.filter(
                    user=user,
                    type_token='sms',
                    used=False
                )
                print(f"✅ Tokens OTP trouvés: {tokens.count()}")

                if tokens.exists():
                    token_obj = tokens.first()
                    print(f"✅ Token hash: {token_obj.token[:20]}...")
                    print(f"✅ Token data: {token_obj.data}")

                    # Récupérer le token original depuis les données
                    original_token = token_obj.data.get('original_token')
                    if original_token:
                        print(f"✅ Token original pour test: {original_token}")

                        # Tester la vérification OTP
                        verify_data = {
                            'token': original_token,
                            'verification_type': 'sms'
                        }

                        verify_response = client.post(
                            f'/api/auth/admins/{user_id}/verify_admin_otp/',
                            data=json.dumps(verify_data),
                            content_type='application/json',
                            HTTP_AUTHORIZATION=f'Bearer {token}'
                        )

                        print(f"📥 Vérification OTP - Status: {verify_response.status_code}")
                        try:
                            verify_result = verify_response.json()
                            print(f"📥 Réponse: {verify_result}")
                        except:
                            print(f"📥 Réponse brute: {verify_response.content[:500]}")

                    else:
                        print("❌ Token original non trouvé dans les données")
                else:
                    print("❌ Aucun token OTP trouvé")

            except Exception as e:
                print(f"❌ Erreur lors de la vérification des tokens: {str(e)}")
                import traceback
                traceback.print_exc()

        else:
            print(f"❌ Échec création admin: {create_response.content}")
    else:
        print(f"❌ Échec login: {login_response.content}")

except Exception as e:
    print(f"❌ Erreur générale: {str(e)}")
    import traceback
    traceback.print_exc()