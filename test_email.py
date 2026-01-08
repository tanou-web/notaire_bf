#!/usr/bin/env python
"""
Script de test pour la configuration email cPanel
Exécutez avec : python test_email.py
"""

import os
import sys
import django
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

def test_email_configuration():
    """Teste la configuration email actuelle"""

    print("🔍 Test de configuration email cPanel")
    print("=" * 50)

    # Vérifier les paramètres
    email_settings = {
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_USE_SSL': settings.EMAIL_USE_SSL,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
    }

    print("📋 Configuration actuelle :")
    for key, value in email_settings.items():
        if 'PASSWORD' in key:
            print(f"  {key}: {'*' * 8}")
        else:
            print(f"  {key}: {value}")

    print("\n📧 Test d'envoi d'email...")

    # Test d'envoi
    try:
        subject = 'Test Configuration cPanel - Notaire BF'
        html_content = """
        <h2>✅ Test Réussi !</h2>
        <p>Cette configuration cPanel fonctionne correctement.</p>
        <p><strong>Détails du test :</strong></p>
        <ul>
            <li>Hôte : {}</li>
            <li>Port : {}</li>
            <li>SSL : {}</li>
            <li>Utilisateur : {}</li>
        </ul>
        <p>🎉 Votre système d'email est prêt pour la production !</p>
        """.format(
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
            settings.EMAIL_USE_SSL,
            settings.EMAIL_HOST_USER
        )

        text_content = """
        Test Réussi !

        Cette configuration cPanel fonctionne correctement.

        Détails du test :
        - Hôte : {}
        - Port : {}
        - SSL : {}
        - Utilisateur : {}

        Votre système d'email est prêt pour la production !
        """.format(
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
            settings.EMAIL_USE_SSL,
            settings.EMAIL_HOST_USER
        )

        # Demander l'adresse de test
        test_email = input("\n📧 Entrez votre adresse email pour le test : ").strip()

        if not test_email:
            print("❌ Aucune adresse email fournie. Test annulé.")
            return

        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [test_email]
        )
        email.attach_alternative(html_content, "text/html")

        result = email.send()

        if result:
            print("✅ Email envoyé avec succès !"            print(f"📧 Vérifiez votre boîte mail : {test_email}")
            print("💡 Si l'email n'arrive pas, vérifiez :"            print("   - Les paramètres cPanel")
            print("   - Les enregistrements MX/DNS")
            print("   - Le dossier spam")
        else:
            print("❌ Échec de l'envoi d'email")

    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        print("\n🔧 Suggestions de dépannage :")
        print("1. Vérifiez que les comptes email existent dans cPanel")
        print("2. Confirmez le mot de passe du compte email")
        print("3. Vérifiez les ports (465 pour SSL, 587 pour TLS)")
        print("4. Assurez-vous que votre domaine pointe vers le bon serveur")

if __name__ == '__main__':
    test_email_configuration()
