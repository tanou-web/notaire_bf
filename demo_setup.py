#!/usr/bin/env python
"""
Script de démonstration pour Notaire BF
Charge les données d'exemple et configure un environnement de test
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

User = get_user_model()

def load_demo_data():
    """Charge les données de démonstration"""
    print("🚀 Configuration de l'environnement de démonstration Notaire BF")
    print("=" * 60)

    try:
        # Charger les fixtures
        print("📦 Chargement des données d'exemple...")
        execute_from_command_line(['manage.py', 'loaddata', 'fixtures/demo_data.json'])

        print("✅ Données d'exemple chargées avec succès!")

        # Créer des comptes de test supplémentaires
        print("👤 Création des comptes de test...")

        # Compte notaire de démo
        if not User.objects.filter(username='demo_notaire').exists():
            notaire = User.objects.create_user(
                username='demo_notaire',
                email='notaire@demo.bf',
                password='demo123',
                nom='Démonstration',
                prenom='Notaire',
                telephone='+22670444444',
                email_verifie=True,
                telephone_verifie=True
            )
            print(f"   ✅ Notaire démo créé: {notaire.username}")

        # Compte client de démo
        if not User.objects.filter(username='demo_client').exists():
            client = User.objects.create_user(
                username='demo_client',
                email='client@demo.bf',
                password='demo123',
                nom='Démonstration',
                prenom='Client',
                telephone='+22670555555',
                email_verifie=True,
                telephone_verifie=False
            )
            print(f"   ✅ Client démo créé: {client.username}")

        print("✅ Comptes de démonstration créés!")

        # Afficher le résumé
        print("\n📊 RÉSUMÉ DE L'ENVIRONNEMENT DE DÉMO")
        print("-" * 40)

        users_count = User.objects.count()
        demandes_count = 3  # Dans les fixtures
        transactions_count = 3  # Dans les fixtures

        print(f"👥 Utilisateurs: {users_count}")
        print(f"📄 Demandes: {demandes_count}")
        print(f"💳 Transactions: {transactions_count}")
        print(f"🏛️ Membres bureau: 2")
        print(f"📚 Documents: 1")
        print(f"📰 Actualités: 1")

        print("\n🔐 COMPTES DE CONNEXION")
        print("-" * 40)
        print("👑 Administrateur:")
        print("   📧 admin@notaires.bf")
        print("   🔑 demo123")
        print()
        print("🏛️ Notaire démo:")
        print("   📧 notaire@demo.bf")
        print("   🔑 demo123")
        print()
        print("👤 Client démo:")
        print("   📧 client@demo.bf")
        print("   🔑 demo123")

        print("\n🌐 URLS IMPORTANTES")
        print("-" * 40)
        print("🏠 Interface admin: http://localhost:8000/admin/")
        print("📖 Documentation API: http://localhost:8000/swagger/")
        print("🔗 API base: http://localhost:8000/api/")

        print("\n🎯 FONCTIONNALITÉS À TESTER")
        print("-" * 40)
        print("✅ Connexion utilisateur")
        print("✅ Création de demandes")
        print("✅ Paiements (Orange Money/Moov Money)")
        print("✅ Gestion documentaire")
        print("✅ Audit et sécurité")
        print("✅ Interface d'administration")

        print("\n🚀 DÉMARRAGE DU SERVEUR")
        print("-" * 40)
        print("Exécutez: python manage.py runserver")
        print("Puis visitez: http://localhost:8000")

        print("\n" + "=" * 60)
        print("🎉 Environnement de démonstration configuré avec succès!")
        print("✨ Prêt pour la présentation aux acheteurs potentiels!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return False

    return True

def cleanup_demo_data():
    """Nettoie les données de démonstration"""
    print("🧹 Nettoyage des données de démonstration...")

    try:
        # Supprimer les comptes de démo
        User.objects.filter(username__in=['demo_notaire', 'demo_client']).delete()

        # Autres nettoyages possibles
        print("✅ Données de démonstration nettoyées!")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        cleanup_demo_data()
    else:
        load_demo_data()

