#!/usr/bin/env python
"""
Script pour vérifier le déploiement sur Render et diagnostiquer l'erreur 500
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

def check_database():
    """Vérifier l'état de la base de données"""
    print("=== VÉRIFICATION BASE DE DONNÉES ===\n")

    from django.db import connection
    from apps.evenements.models import Evenement, EvenementChamp, Inscription, InscriptionReponse

    try:
        # Test connexion DB
        cursor = connection.cursor()
        print("[OK] Connexion à la base de données établie")

        # Compter les tables
        tables = [
            ('Evenement', Evenement),
            ('EvenementChamp', EvenementChamp),
            ('Inscription', Inscription),
            ('InscriptionReponse', InscriptionReponse)
        ]

        for table_name, model in tables:
            count = model.objects.count()
            print(f"[INFO] Table {table_name}: {count} enregistrements")

        # Vérifier les événements actifs
        evenements_actifs = Evenement.objects.filter(actif=True)
        print(f"[INFO] Événements actifs: {evenements_actifs.count()}")

        for event in evenements_actifs:
            champs_count = event.champs.filter(actif=True).count()
            inscriptions_count = Inscription.objects.filter(evenement=event).count()
            print(f"  - {event.titre} (ID: {event.id}): {champs_count} champs, {inscriptions_count} inscriptions")

    except Exception as e:
        print(f"[ERROR] Problème base de données: {e}")
        import traceback
        traceback.print_exc()

def check_settings():
    """Vérifier les settings critiques"""
    print("\n=== VÉRIFICATION SETTINGS ===\n")

    from django.conf import settings

    # Vérifier les settings CORS
    print(f"CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', 'NOT SET')}")
    print(f"CORS_ALLOWED_ORIGINS: {getattr(settings, 'CORS_ALLOWED_ORIGINS', 'NOT SET')}")

    # Vérifier DEBUG
    print(f"DEBUG: {getattr(settings, 'DEBUG', 'NOT SET')}")

    # Vérifier DATABASE
    database_settings = getattr(settings, 'DATABASES', {}).get('default', {})
    db_engine = database_settings.get('ENGINE', 'NOT SET')
    print(f"DATABASE ENGINE: {db_engine}")

    # Vérifier si on utilise SQLite (problématique sur Render)
    if 'sqlite' in db_engine.lower():
        print("[WARNING] Utilisation de SQLite - peut causer des problèmes de concurrence sur Render")
    else:
        print("[OK] Base de données non-SQLite détectée")

def check_migrations():
    """Vérifier l'état des migrations"""
    print("\n=== VÉRIFICATION MIGRATIONS ===\n")

    from django.core.management import execute_from_command_line

    try:
        # Simuler la commande showmigrations
        from django.core.management.commands.showmigrations import Command as ShowMigrationsCommand
        from io import StringIO

        cmd = ShowMigrationsCommand()
        stdout = StringIO()
        cmd.stdout = stdout
        cmd.handle(verbosity=1, app_labels=['evenements'])

        output = stdout.getvalue()
        print("Migrations événements:")
        print(output)

        # Vérifier si toutes les migrations sont appliquées
        if '[ ]' in output:
            print("[WARNING] Certaines migrations ne sont pas appliquées!")
        else:
            print("[OK] Toutes les migrations événements sont appliquées")

    except Exception as e:
        print(f"[ERROR] Erreur vérification migrations: {e}")

def test_serializer_edge_cases():
    """Tester les cas limites du serializer"""
    print("\n=== TEST CAS LIMITES SERIALIZER ===\n")

    from apps.evenements.models import Evenement, EvenementChamp
    from apps.evenements.serializers import InscriptionCreateSerializer

    # Créer un événement de test
    try:
        evenement = Evenement.objects.create(
            titre='Test Edge Cases',
            nombre_places=1,
            statut='ouvert'
        )

        champ = EvenementChamp.objects.create(
            evenement=evenement,
            label='Test',
            type='text',
            obligatoire=True,
            ordre=1
        )

        # Test avec places = 0
        print("Test 1: Événement complet (0 places)")
        evenement.nombre_places = 0
        evenement.save()

        data = {
            "evenement": evenement.id,
            "nom": "Test",
            "prenom": "User",
            "email": "test@example.com",
            "telephone": "0123456789",
            "reponses": [{"champ": champ.id, "valeur": "test"}]
        }

        serializer = InscriptionCreateSerializer(data=data)
        is_valid = serializer.is_valid()
        print(f"Événement complet - valide: {is_valid}")
        if not is_valid:
            print(f"Erreurs: {serializer.errors}")

        # Remettre à 1 place
        evenement.nombre_places = 1
        evenement.save()

        # Test création normale
        print("\nTest 2: Création normale")
        serializer = InscriptionCreateSerializer(data=data)
        if serializer.is_valid():
            inscription = serializer.save()
            print(f"[OK] Inscription créée: {inscription.id}")
        else:
            print(f"[ERROR] Erreurs: {serializer.errors}")

        # Nettoyer
        evenement.delete()

    except Exception as e:
        print(f"[ERROR] Test edge cases: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=== DIAGNOSTIC ERREUR 500 SUR RENDER ===\n")

    check_database()
    check_settings()
    check_migrations()
    test_serializer_edge_cases()

    print("\n=== RECOMMANDATIONS POUR RENDER ===\n")
    print("1. Vérifiez les logs Render pour l'erreur détaillée:")
    print("   - Allez dans le dashboard Render > Service > Logs")
    print("   - Cherchez l'erreur complète (pas juste '500 Internal Server Error')")
    print()
    print("2. Variables d'environnement à vérifier sur Render:")
    print("   - DJANGO_SETTINGS_MODULE")
    print("   - DATABASE_URL")
    print("   - SECRET_KEY")
    print("   - DEBUG=False")
    print()
    print("3. Migrations à appliquer:")
    print("   - Dans Render shell: python manage.py migrate")
    print()
    print("4. Redémarrer le service Render après changements")

    print("\n=== DIAGNOSTIC TERMINÉ ===")
