#!/usr/bin/env python
"""
Script de test pour l'inscription et l'envoi SMS OTP
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.utilisateurs.models import VerificationVerificationtoken
from apps.communications.models import CommunicationsSmslog
from apps.communications.services import SMSService
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_configuration_sms():
    """Test 1: Vérifier la configuration SMS"""
    print_header("TEST 1: CONFIGURATION SMS")
    
    token = getattr(settings, 'AQILAS_TOKEN', None)
    sender = getattr(settings, 'AQILAS_SENDER', None)
    provider = getattr(settings, 'SMS_PROVIDER', None)
    
    print(f"SMS Provider: {provider}")
    print(f"AQILAS_TOKEN: {'DEFINI' if token else 'NON DEFINI'}")
    print(f"AQILAS_SENDER: {sender}")
    
    if token:
        print(f"Token (debut): {token[:10]}...")
        print("\nOK: Configuration SMS active")
        return True
    else:
        print("\nERREUR: AQILAS_TOKEN non defini dans .env")
        print("Action: Decommenter AQILAS_TOKEN dans .env")
        return False

def test_generation_jwt():
    """Test 2: Génération de tokens JWT"""
    print_header("TEST 2: GENERATION TOKEN JWT")
    
    try:
        # Créer ou récupérer un utilisateur de test
        user, created = User.objects.get_or_create(
            username='test_jwt',
            defaults={
                'email': 'test_jwt@example.com',
                'nom': 'Test',
                'prenom': 'JWT',
                'telephone': '+22670000000',
                'email_verifie': True,
                'is_active': True
            }
        )
        if created:
            user.set_password('Test123!@#')
            user.save()
        
        # Générer un token JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"Utilisateur: {user.username}")
        print(f"Access Token genere: {access_token[:50]}...")
        print(f"Refresh Token genere: {str(refresh)[:50]}...")
        print("\nOK: Tokens JWT generes avec succes")
        return True
    except Exception as e:
        print(f"\nERREUR: {e}")
        return False

def test_generation_otp():
    """Test 3: Génération de token OTP"""
    print_header("TEST 3: GENERATION TOKEN OTP")
    
    try:
        from apps.utilisateurs.serializers import VerificationTokenGenerator
        
        # Générer un OTP
        otp = VerificationTokenGenerator.generate_otp(6)
        otp_hash = VerificationTokenGenerator.hash_token(otp)
        
        print(f"OTP genere: {otp}")
        print(f"Hash cree: {otp_hash[:30]}...")
        print("\nOK: Token OTP genere avec succes")
        return True
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_envoi_sms():
    """Test 4: Test d'envoi SMS"""
    print_header("TEST 4: ENVOI SMS")
    
    test_phone = "+22670000000"
    test_otp = "123456"
    
    print(f"Numero de test: {test_phone}")
    print(f"OTP de test: {test_otp}")
    print("\nEnvoi en cours...")
    
    try:
        success, message_id, error = SMSService.send_verification_sms(
            phone_number=test_phone,
            token=test_otp,
            user_name="Test User"
        )
        
        print(f"\nResultat:")
        print(f"  Success: {success}")
        print(f"  Message ID: {message_id}")
        print(f"  Erreur: {error}")
        
        # Vérifier dans les logs
        last_sms = CommunicationsSmslog.objects.last()
        if last_sms:
            print(f"\nLog SMS:")
            print(f"  Destinataire: {last_sms.destinataire}")
            print(f"  Statut: {last_sms.statut}")
            print(f"  Message ID: {last_sms.message_id}")
            print(f"  Erreur: {last_sms.erreur}")
        
        if success:
            print("\nOK: SMS envoye avec succes")
            return True
        else:
            print(f"\nERREUR: Echec envoi SMS - {error}")
            print("Vérifier:")
            print("  - Token AQILAS valide")
            print("  - Credits SMS sur compte Aqilas")
            print("  - Numero au format +226XXXXXXXXX")
            return False
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_inscription():
    """Test 5: Test API d'inscription"""
    print_header("TEST 5: API INSCRIPTION")
    
    client = APIClient()
    
    import random
    username = f"test_{random.randint(1000, 9999)}"
    
    data = {
        "username": username,
        "email": f"{username}@example.com",
        "telephone": "+22670000000",
        "password": "Test123!@#",
        "password_confirmation": "Test123!@#",
        "nom": "Test",
        "prenom": "API",
        "accept_terms": True
    }
    
    print(f"Inscription avec username: {username}")
    print("Envoi requete...")
    
    try:
        response = client.post('/api/auth/register/', data, format='json')
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        if response.status_code == 201:
            print("\nOK: Inscription reussie")
            
            # Vérifier en base
            user = User.objects.get(username=username)
            print(f"Utilisateur cree: {user.username}")
            print(f"Actif: {user.is_active}")
            print(f"Email verifie: {user.email_verifie}")
            
            # Vérifier token OTP créé
            token = VerificationVerificationtoken.objects.filter(
                user=user,
                type_token='telephone',
                used=False
            ).first()
            
            if token:
                print(f"\nToken OTP cree (expire le: {token.expires_at})")
            
            # Vérifier SMS log
            sms_log = CommunicationsSmslog.objects.filter(
                destinataire=user.telephone
            ).order_by('-created_at').first()
            
            if sms_log:
                print(f"\nSMS Log:")
                print(f"  Statut: {sms_log.statut}")
                print(f"  Message ID: {sms_log.message_id}")
                if sms_log.erreur:
                    print(f"  Erreur: {sms_log.erreur}")
            
            return True
        else:
            print(f"\nERREUR: {response.data}")
            return False
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_login():
    """Test 6: Test API de login"""
    print_header("TEST 6: API LOGIN")
    
    client = APIClient()
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_login_api',
        defaults={
            'email': 'test_login@example.com',
            'nom': 'Test',
            'prenom': 'Login',
            'telephone': '+22670000001',
            'email_verifie': True,
            'is_active': True
        }
    )
    if created:
        user.set_password('Test123!@#')
        user.save()
    
    data = {
        "username": "test_login_api",
        "password": "Test123!@#"
    }
    
    print("Test login...")
    
    try:
        response = client.post('/api/token/', data, format='json')
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.data
            print(f"Access Token: {result.get('access', '')[:50]}...")
            print(f"Refresh Token: {result.get('refresh', '')[:50]}...")
            print("\nOK: Login reussi, tokens JWT generes")
            return True
        else:
            print(f"ERREUR: {response.data}")
            return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def main():
    """Exécuter tous les tests"""
    print("=" * 60)
    print("  TESTS D'AUTHENTIFICATION ET SMS - NOTAIRES BF")
    print("=" * 60)
    
    results = []
    
    # Exécuter les tests
    results.append(("Configuration SMS", test_configuration_sms()))
    results.append(("Generation JWT", test_generation_jwt()))
    results.append(("Generation OTP", test_generation_otp()))
    
    # Demander si l'utilisateur veut tester l'envoi SMS réel
    print("\n" + "=" * 60)
    print("  TESTS AVEC ENVOI SMS REEL")
    print("=" * 60)
    print("\nATTENTION: Les tests suivants vont envoyer de vrais SMS")
    print("(coûts possibles selon votre plan Aqilas)")
    
    response = input("\nContinuer avec les tests d'envoi SMS? (o/n): ")
    
    if response.lower() == 'o':
        results.append(("Envoi SMS", test_envoi_sms()))
        results.append(("API Inscription", test_api_inscription()))
    else:
        print("\nTests d'envoi SMS skippes")
        results.append(("Envoi SMS", None))
        results.append(("API Inscription", None))
    
    results.append(("API Login", test_api_login()))
    
    # Résumé
    print_header("RESUME DES TESTS")
    
    for test_name, result in results:
        if result is None:
            status = "SKIPPE"
        elif result:
            status = "OK"
        else:
            status = "ERREUR"
        print(f"{test_name:.<30} {status}")
    
    print("\n" + "=" * 60)
    print("  FIN DES TESTS")
    print("=" * 60)

if __name__ == "__main__":
    main()
