from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Migre les images du stockage local vers le stockage cloud configuré'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule la migration sans effectuer de changements',
        )
        parser.add_argument(
            '--delete-local',
            action='store_true',
            help='Supprime les fichiers locaux après migration réussie',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_local = options['delete_local']

        # Vérifier que nous ne sommes pas en mode DEBUG (développement)
        if settings.DEBUG:
            self.stdout.write(
                self.style.WARNING(
                    'ATTENTION: Vous êtes en mode développement (DEBUG=True). '
                    'Cette commande est destinée à la production uniquement.'
                )
            )
            return

        # Vérifier que le stockage cloud est configuré
        if hasattr(settings, 'DEFAULT_FILE_STORAGE'):
            if 'cloudinary' in settings.DEFAULT_FILE_STORAGE.lower():
                storage_type = 'Cloudinary'
            elif 's3' in settings.DEFAULT_FILE_STORAGE.lower():
                storage_type = 'AWS S3'
            else:
                storage_type = 'Stockage cloud personnalisé'
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Aucun stockage cloud configuré. Vérifiez vos variables d\'environnement.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Migration vers {storage_type} - Mode dry-run: {dry_run}')
        )

        media_root = Path(settings.MEDIA_ROOT.replace('media/', '')) / 'media' if not settings.DEBUG else Path(settings.MEDIA_ROOT)

        if not media_root.exists():
            self.stdout.write(
                self.style.WARNING(f'Dossier media introuvable: {media_root}')
            )
            return

        # Collecter tous les fichiers images
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        image_files = []

        for ext in image_extensions:
            image_files.extend(list(media_root.rglob(f'*{ext}')))
            image_files.extend(list(media_root.rglob(f'*{ext.upper()}')))

        if not image_files:
            self.stdout.write(
                self.style.WARNING('Aucune image trouvée dans le dossier media')
            )
            return

        self.stdout.write(f'Images trouvées: {len(image_files)}')

        migrated_count = 0
        error_count = 0

        for image_path in image_files:
            # Chemin relatif par rapport au MEDIA_ROOT
            relative_path = image_path.relative_to(media_root)

            try:
                with open(image_path, 'rb') as f:
                    file_content = f.read()

                if not dry_run:
                    # Uploader vers le stockage cloud
                    cloud_path = f'media/{relative_path}'
                    saved_path = default_storage.save(cloud_path, image_path)

                    self.stdout.write(
                        f'✓ Migré: {relative_path} -> {saved_path}'
                    )
                else:
                    self.stdout.write(
                        f'[DRY-RUN] Serait migré: {relative_path}'
                    )

                migrated_count += 1

                # Supprimer le fichier local si demandé
                if not dry_run and delete_local:
                    image_path.unlink()
                    self.stdout.write(f'  - Supprimé localement: {relative_path}')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Erreur pour {relative_path}: {str(e)}')
                )
                error_count += 1

        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Migration terminée: {migrated_count} images migrées')
        )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Erreurs: {error_count}')
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'Ceci était un dry-run. Utilisez --dry-run=False pour migrer réellement.'
                )
            )