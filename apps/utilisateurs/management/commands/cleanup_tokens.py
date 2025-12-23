from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.utilisateurs.models import VerificationVerificationtoken
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Nettoie les tokens de vérification expirés'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans le faire',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Tokens expirés et non utilisés
        expired_tokens = VerificationVerificationtoken.objects.filter(
            expires_at__lt=timezone.now(),
            used=False
        )
        
        count = expired_tokens.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: {count} tokens expirés seraient supprimés')
            )
            for token in expired_tokens[:10]:  # Afficher les 10 premiers
                self.stdout.write(f'  - Token #{token.id} pour {token.user} expiré le {token.expires_at}')
        else:
            deleted_count, _ = expired_tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{deleted_count} tokens expirés ont été supprimés')
            )
            logger.info(f'Cleanup: {deleted_count} tokens expirés supprimés')
        
        # Tokens utilisés (on peut les garder pour audit ou les supprimer après un certain temps)
        old_used_tokens = VerificationVerificationtoken.objects.filter(
            used=True,
            updated_at__lt=timezone.now() - timezone.timedelta(days=30)
        )
        
        old_count = old_used_tokens.count()
        
        if not dry_run and old_count > 0:
            old_used_tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{old_count} anciens tokens utilisés ont été supprimés')
            )
            logger.info(f'Cleanup: {old_count} anciens tokens utilisés supprimés')