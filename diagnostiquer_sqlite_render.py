#!/usr/bin/env python
"""
Diagnostiquer le problème SQLite sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

def diagnostiquer_sqlite():
    print("=== DIAGNOSTIC SQLITE SUR RENDER ===\n")

    from django.db import connection
    from django.conf import settings
    import sqlite3

    # 1. Vérifier la configuration DB
    print("1. Configuration base de données :")
    db_config = settings.DATABASES['default']
    print(f"   ENGINE: {db_config['ENGINE']}")
    print(f"   NAME: {db_config['NAME']}")
    print(f"   Chemin absolu: {os.path.abspath(db_config['NAME'])}")

    # 2. Vérifier si le fichier existe
    db_path = str(db_config['NAME'])
    print(f"\n2. État du fichier DB :")
    print(f"   Existe: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"   Taille: {size} bytes")
        try:
            mtime = os.path.getmtime(db_path)
            from datetime import datetime
            print(f"   Dernière modification: {datetime.fromtimestamp(mtime)}")
        except:
            print("   Impossible de lire la date de modification")

    # 3. Tester la connexion
    print(f"\n3. Test de connexion Django :")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"   Version SQLite: {version}")
        print("   [OK] Connexion Django OK")
    except Exception as e:
        print(f"   [ERROR] Erreur connexion Django: {e}")

    # 4. Tester connexion directe SQLite
    print(f"\n4. Test connexion directe SQLite :")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"   Version SQLite: {version}")

        # Tester les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tables trouvées: {len(tables)}")
        for table in tables:
            print(f"     - {table[0]}")

        conn.close()
        print("   [OK] Connexion directe SQLite OK")
    except Exception as e:
        print(f"   [ERROR] Erreur connexion directe SQLite: {e}")

    # 5. Vérifier les permissions
    print(f"\n5. Permissions du dossier :")
    db_dir = os.path.dirname(db_path)
    print(f"   Dossier DB: {db_dir}")

    try:
        print(f"   Dossier existe: {os.path.exists(db_dir)}")
        print(f"   Dossier accessible en écriture: {os.access(db_dir, os.W_OK)}")
        if os.path.exists(db_path):
            print(f"   Fichier accessible en écriture: {os.access(db_path, os.W_OK)}")
    except Exception as e:
        print(f"   Erreur vérification permissions: {e}")

    # 6. Vérifier les variables d'environnement
    print(f"\n6. Variables d'environnement :")
    env_vars = ['DATABASE_URL', 'RENDER', 'RENDER_SERVICE_ID', 'RENDER_INSTANCE_ID']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Masquer les mots de passe dans DATABASE_URL
            if var == 'DATABASE_URL' and '://' in value:
                parts = value.split('://')
                if '@' in parts[1]:
                    auth, rest = parts[1].split('@', 1)
                    if ':' in auth:
                        user, pwd = auth.split(':', 1)
                        value = f"{parts[0]}://{user}:***@{rest}"
            print(f"   {var}: {value}")
        else:
            print(f"   {var}: Non défini")

    # 7. Test des opérations de base
    print(f"\n7. Test opérations DB :")
    from apps.evenements.models import Evenement

    try:
        # Test SELECT
        count = Evenement.objects.count()
        print(f"   [OK] SELECT OK - {count} evenements")

        # Test INSERT
        event_test = Evenement.objects.create(
            titre='Test Render',
            nombre_places=1,
            statut='ouvert'
        )
        print(f"   [OK] INSERT OK - ID: {event_test.id}")

        # Test UPDATE
        event_test.nombre_places = 2
        event_test.save()
        print("   [OK] UPDATE OK")

        # Test DELETE
        event_test.delete()
        print("   [OK] DELETE OK")

    except Exception as e:
        print(f"   [ERROR] Erreur opération DB: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n=== DIAGNOSTIC TERMINÉ ===")

def recommandations_render():
    print("\n=== RECOMMANDATIONS POUR SQLITE SUR RENDER ===\n")

    print("[PROBLEMES] PROBLEMES POTENTIELS AVEC SQLITE SUR RENDER :")
    print("1. Le fichier DB n'est PAS persistant entre deploiements")
    print("2. Chemin d'acces peut ne pas etre accessible en ecriture")
    print("3. Problemes de concurrence avec plusieurs instances")
    print("4. Limites de stockage sur le plan gratuit")
    print()
    print("[SOLUTIONS] SOLUTIONS RECOMMANDEES :")
    print("1. Utiliser une vraie base de donnees (PostgreSQL/MySQL)")
    print("2. Ou utiliser un stockage persistant (AWS S3, etc.)")
    print("3. Ou basculer vers un plan Render payant")
    print()
    print("[TRAVAIL] POUR CONTINUER AVEC SQLITE (NON RECOMMANDE) :")
    print("1. Verifier que le dossier parent est accessible en ecriture")
    print("2. Utiliser un chemin absolu pour la DB")
    print("3. Desactiver la concurrence (1 instance seulement)")
    print("4. Sauvegarder la DB localement et la recharger sur Render")

if __name__ == '__main__':
    diagnostiquer_sqlite()
    recommandations_render()
