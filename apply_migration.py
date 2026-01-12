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

    from django.db import connection
    from django.core.management import execute_from_command_line

    print("\n=== APPLICATION MIGRATION ===")

    # Vérifier l'état des migrations
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, name, applied
            FROM django_migrations
            WHERE app = 'utilisateurs'
            ORDER BY applied DESC;
        """)
        migrations = cursor.fetchall()

        print("Migrations utilisateurs appliquées:")
        for app, name, applied in migrations:
            status = "✅" if applied else "❌"
            print(f"  {status} {name}")

    # Appliquer la migration manuellement si nécessaire
    print("\n=== APPLICATION MANUELLE ===")

    try:
        # Vérifier si la colonne 'used' existe déjà
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(verification_verificationtoken);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'used' not in column_names:
                print("❌ Colonne 'used' manquante - Ajout en cours...")

                # Ajouter la colonne manuellement
                cursor.execute("ALTER TABLE verification_verificationtoken ADD COLUMN used BOOLEAN DEFAULT 0;")
                print("✅ Colonne 'used' ajoutée avec succès")
            else:
                print("✅ Colonne 'used' existe déjà")

    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {str(e)}")

    # Vérifier que la migration est marquée comme appliquée
    try:
        from django.db.migrations.recorder import MigrationRecorder
        migration_recorder = MigrationRecorder(connection)

        migration_applied = migration_recorder.migration_qs.filter(
            app='utilisateurs',
            name='0002_add_used_field'
        ).exists()

        if not migration_applied:
            print("❌ Migration non marquée comme appliquée - Marquage en cours...")
            # Marquer la migration comme appliquée
            migration_recorder.record_applied('utilisateurs', '0002_add_used_field')
            print("✅ Migration marquée comme appliquée")
        else:
            print("✅ Migration déjà marquée comme appliquée")

    except Exception as e:
        print(f"❌ Erreur lors du marquage de la migration: {str(e)}")

    print("\n=== VÉRIFICATION FINALE ===")

    # Test final
    try:
        from apps.utilisateurs.models import VerificationVerificationtoken

        # Créer un token de test
        test_token = VerificationVerificationtoken.objects.create(
            user_id=1,  # Utilisateur admin par défaut
            token='test_hash_final',
            type_token='sms',
            used=False,
            expires_at=django.utils.timezone.now() + django.utils.timezone.timedelta(minutes=10),
            data={'test': 'final'}
        )

        print(f"✅ Token de test créé avec succès (ID: {test_token.id})")

        # Tester la recherche avec used=False
        found = VerificationVerificationtoken.objects.filter(used=False).count()
        print(f"✅ Tokens trouvés avec used=False: {found}")

        # Nettoyer
        test_token.delete()
        print("✅ Test réussi - Migration appliquée correctement")

    except Exception as e:
        print(f"❌ Erreur lors du test final: {str(e)}")

except Exception as e:
    print(f"❌ Erreur générale: {str(e)}")
    import traceback
    traceback.print_exc()