#!/usr/bin/env python
"""
Script de diagnostic complet du système OTP
"""
import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

def check_django_setup():
    """Vérifier que Django se configure correctement"""
    print("🔍 Vérification de la configuration Django...")
    try:
        django.setup()
        print("✅ Django configuré avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur de configuration Django: {str(e)}")
        return False

def check_models():
    """Vérifier les modèles et leurs champs"""
    print("\n🔍 Vérification des modèles...")
    try:
        from apps.utilisateurs.models import User, VerificationVerificationtoken

        # Vérifier le modèle User
        user_fields = [f.name for f in User._meta.fields]
        print(f"✅ Modèle User - Champs: {user_fields}")

        # Vérifier le modèle VerificationVerificationtoken
        token_fields = [f.name for f in VerificationVerificationtoken._meta.fields]
        print(f"✅ Modèle VerificationVerificationtoken - Champs: {token_fields}")

        # Vérifier que le champ 'used' existe
        if 'used' in token_fields:
            print("✅ Champ 'used' trouvé dans VerificationVerificationtoken")
        else:
            print("❌ Champ 'used' MANQUANT dans VerificationVerificationtoken")
            return False

        return True
    except Exception as e:
        print(f"❌ Erreur dans les modèles: {str(e)}")
        return False

def check_imports():
    """Vérifier tous les imports critiques"""
    print("\n🔍 Vérification des imports...")
    try:
        from apps.utilisateurs.views import AdminManagementViewSet
        from apps.utilisateurs.serializers import AdminCreateSerializer, VerifyTokenSerializer
        from apps.communications.services import SMSService
        from apps.utilisateurs.serializers import VerificationTokenGenerator

        print("✅ Tous les imports réussis")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue lors des imports: {str(e)}")
        return False

def check_migrations():
    """Vérifier l'état des migrations"""
    print("\n🔍 Vérification des migrations...")
    try:
        from django.core.management import execute_from_command_line
        from django.db import connection

        # Vérifier si la table existe
        tables = connection.introspection.table_names()
        if 'verification_verificationtoken' in tables:
            print("✅ Table 'verification_verificationtoken' existe")

            # Vérifier les colonnes
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(verification_verificationtoken)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"✅ Colonnes de la table: {column_names}")

                if 'used' in column_names:
                    print("✅ Colonne 'used' existe dans la base de données")
                else:
                    print("❌ Colonne 'used' MANQUANTE dans la base de données")
                    return False
        else:
            print("❌ Table 'verification_verificationtoken' n'existe pas")
            return False

        return True
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des migrations: {str(e)}")
        return False

def check_views():
    """Vérifier que les vues se chargent correctement"""
    print("\n🔍 Vérification des vues...")
    try:
        from apps.utilisateurs.views import AdminManagementViewSet
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        view = AdminManagementViewSet()

        # Vérifier que les actions existent
        if hasattr(view, 'verify_admin_otp'):
            print("✅ Action 'verify_admin_otp' existe")
        else:
            print("❌ Action 'verify_admin_otp' MANQUANTE")
            return False

        print("✅ Vues chargées correctement")
        return True
    except Exception as e:
        print(f"❌ Erreur dans les vues: {str(e)}")
        return False

def run_diagnostic():
    """Exécuter tous les diagnostics"""
    print("🚀 DIAGNOSTIC COMPLET DU SYSTÈME OTP")
    print("=" * 50)

    checks = [
        check_django_setup,
        check_models,
        check_imports,
        check_migrations,
        check_views
    ]

    results = []
    for check in checks:
        results.append(check())

    print("\n" + "=" * 50)
    print("📊 RÉSULTATS DU DIAGNOSTIC")

    passed = sum(results)
    total = len(results)

    print(f"✅ Tests réussis: {passed}/{total}")

    if passed == total:
        print("🎉 SYSTÈME OTP OPÉRATIONNEL !")
        return True
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS - Nécessite correction")
        return False

if __name__ == '__main__':
    success = run_diagnostic()
    sys.exit(0 if success else 1)