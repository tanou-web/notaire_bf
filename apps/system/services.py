from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import json
import logging
import hashlib
import secrets
from cryptography.fernet import Fernet
import psutil
import socket
import os

logger = logging.getLogger(__name__)


class SystemService:
    """Service de gestion système."""
    
    @staticmethod
    def get_config(key, default=None):
        """Récupère une configuration système."""
        from .models import SystemConfig
        
        try:
            config = SystemConfig.objects.get(key=key)
            return config.get_value()
        except SystemConfig.DoesNotExist:
            # Chercher dans les settings Django
            return getattr(settings, key, default)
    
    @staticmethod
    def set_config(key, value, value_type='string', category='general', **kwargs):
        """Définit une configuration système."""
        from .models import SystemConfig
        
        config, created = SystemConfig.objects.get_or_create(
            key=key,
            defaults={
                'value_type': value_type,
                'category': category,
                **kwargs
            }
        )
        
        config.set_value(value)
        config.save()
        return config
    
    @staticmethod
    def get_all_configs(category=None):
        """Récupère toutes les configurations."""
        from .models import SystemConfig
        
        queryset = SystemConfig.objects.all()
        if category:
            queryset = queryset.filter(category=category)
        
        configs = {}
        for config in queryset:
            configs[config.key] = config.get_value()
        
        return configs


class LoggingService:
    """Service de journalisation."""
    
    @staticmethod
    def info(source, module, action, message, **kwargs):
        """Log un message d'information."""
        from .models import SystemLog
        return SystemLog.log('info', source, module, action, message, **kwargs)
    
    @staticmethod
    def warning(source, module, action, message, **kwargs):
        """Log un message d'avertissement."""
        from .models import SystemLog
        return SystemLog.log('warning', source, module, action, message, **kwargs)
    
    @staticmethod
    def error(source, module, action, message, **kwargs):
        """Log un message d'erreur."""
        from .models import SystemLog
        return SystemLog.log('error', source, module, action, message, **kwargs)
    
    @staticmethod
    def critical(source, module, action, message, **kwargs):
        """Log un message critique."""
        from .models import SystemLog
        return SystemLog.log('critical', source, module, action, message, **kwargs)
    
    @staticmethod
    def cleanup_old_logs(days=90, level=None):
        """Nettoie les anciens logs."""
        from .models import SystemLog
        
        cutoff_date = timezone.now() - timedelta(days=days)
        queryset = SystemLog.objects.filter(timestamp__lt=cutoff_date)
        
        if level:
            queryset = queryset.filter(level=level)
        
        deleted_count, _ = queryset.delete()
        return deleted_count
    
    @staticmethod
    def get_log_stats(hours=24):
        """Récupère les statistiques des logs."""
        from .models import SystemLog
        from django.db.models import Count
        
        since = timezone.now() - timedelta(hours=hours)
        
        stats = {
            'total': SystemLog.objects.filter(timestamp__gte=since).count(),
            'by_level': dict(SystemLog.objects.filter(
                timestamp__gte=since
            ).values('level').annotate(
                count=Count('id')
            ).values_list('level', 'count')),
            'by_source': dict(SystemLog.objects.filter(
                timestamp__gte=since
            ).values('source').annotate(
                count=Count('id')
            ).values_list('source', 'count')),
        }
        
        return stats


class MonitoringService:
    """Service de monitoring."""
    
    @staticmethod
    def collect_system_metrics():
        """Collecte les métriques système."""
        from .models import SystemMetric
        
        metrics = []
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(SystemMetric(
            metric_type='cpu',
            name='cpu_usage',
            value=cpu_percent,
            unit='%'
        ))
        
        # Mémoire
        memory = psutil.virtual_memory()
        metrics.append(SystemMetric(
            metric_type='memory',
            name='memory_used',
            value=memory.used / (1024**3),  # GB
            unit='GB'
        ))
        metrics.append(SystemMetric(
            metric_type='memory',
            name='memory_percent',
            value=memory.percent,
            unit='%'
        ))
        
        # Disque
        disk = psutil.disk_usage('/')
        metrics.append(SystemMetric(
            metric_type='disk',
            name='disk_used',
            value=disk.used / (1024**3),  # GB
            unit='GB'
        ))
        metrics.append(SystemMetric(
            metric_type='disk',
            name='disk_percent',
            value=disk.percent,
            unit='%'
        ))
        
        # Enregistrer les métriques
        SystemMetric.objects.bulk_create(metrics)
        return len(metrics)
    
    @staticmethod
    def check_service_health(service_name, check_function, **kwargs):
        """Vérifie la santé d'un service."""
        from .models import SystemHealth
        
        start_time = timezone.now()
        try:
            result = check_function(**kwargs)
            response_time = (timezone.now() - start_time).total_seconds() * 1000
            
            health, created = SystemHealth.objects.update_or_create(
                service=service_name,
                defaults={
                    'status': 'healthy',
                    'last_check': timezone.now(),
                    'response_time': response_time,
                    'details': {'result': result} if result else {}
                }
            )
            
            return health
        except Exception as e:
            health, created = SystemHealth.objects.update_or_create(
                service=service_name,
                defaults={
                    'status': 'unhealthy',
                    'last_check': timezone.now(),
                    'error_message': str(e),
                    'details': {'error': str(e)}
                }
            )
            
            LoggingService.error(
                'system',
                'monitoring',
                'health_check_failed',
                f"Échec de la vérification de santé pour {service_name}: {str(e)}"
            )
            
            return health
    
    @staticmethod
    def get_system_status():
        """Récupère le statut global du système."""
        from .models import SystemHealth
        
        services = SystemHealth.objects.all()
        healthy_count = services.filter(status='healthy').count()
        total_count = services.count()
        
        status = {
            'overall': 'unknown',
            'healthy_services': healthy_count,
            'total_services': total_count,
            'services': {}
        }
        
        if total_count == 0:
            status['overall'] = 'unknown'
        elif healthy_count == total_count:
            status['overall'] = 'healthy'
        elif services.filter(status='unhealthy').exists():
            status['overall'] = 'unhealthy'
        else:
            status['overall'] = 'degraded'
        
        for service in services:
            status['services'][service.service] = {
                'status': service.status,
                'last_check': service.last_check,
                'response_time': service.response_time
            }
        
        return status


class EncryptionService:
    """Service de chiffrement."""
    
    _fernet = None
    
    @classmethod
    def _get_fernet(cls):
        """Initialise Fernet avec la clé de settings."""
        if cls._fernet is None:
            key = getattr(settings, 'ENCRYPTION_KEY', None)
            if not key:
                # Générer une clé si non configurée
                key = Fernet.generate_key()
                logger.warning(
                    "ENCRYPTION_KEY non configurée, utilisation d'une clé temporaire"
                )
            cls._fernet = Fernet(key)
        return cls._fernet
    
    @staticmethod
    def encrypt(data):
        """Chiffre des données."""
        if not data:
            return data
        
        fernet = EncryptionService._get_fernet()
        if isinstance(data, str):
            data = data.encode()
        
        return fernet.encrypt(data).decode()
    
    @staticmethod
    def decrypt(encrypted_data):
        """Déchiffre des données."""
        if not encrypted_data:
            return encrypted_data
        
        fernet = EncryptionService._get_fernet()
        return fernet.decrypt(encrypted_data.encode()).decode()


class TaskScheduler:
    """Service de planification des tâches."""
    
    @staticmethod
    def calculate_next_run(schedule):
        """Calcule la prochaine exécution selon une expression cron."""
        # Implémentation basique - utiliser une lib comme croniter en production
        if schedule == 'hourly':
            return timezone.now() + timedelta(hours=1)
        elif schedule == 'daily':
            return timezone.now() + timedelta(days=1)
        elif schedule == 'weekly':
            return timezone.now() + timedelta(weeks=1)
        elif schedule == 'monthly':
            return timezone.now() + timedelta(days=30)
        else:
            # Essayer de parser une expression cron simple
            return timezone.now() + timedelta(hours=1)
    
    @staticmethod
    def execute_task(task):
        """Exécute une tâche planifiée."""
        from .models import ScheduledTask, SystemLog
        
        start_time = timezone.now()
        
        try:
            # Simuler l'exécution
            # En production, vous utiliseriez subprocess ou Celery
            result = f"Tâche exécutée: {task.command}"
            
            task.last_run = timezone.now()
            task.last_result = result
            task.last_duration = (timezone.now() - start_time).total_seconds() * 1000
            task.retry_count = 0
            task.save()
            
            SystemLog.info(
                'system',
                'task_scheduler',
                'task_executed',
                f"Tâche exécutée: {task.name}",
                details={'task_id': task.id, 'result': result}
            )
            
            return result
            
        except Exception as e:
            task.last_run = timezone.now()
            task.last_result = str(e)
            task.retry_count += 1
            
            if task.retry_count >= task.max_retries:
                task.status = 'failed'
            
            task.save()
            
            SystemLog.error(
                'system',
                'task_scheduler',
                'task_failed',
                f"Échec de la tâche: {task.name}",
                details={'task_id': task.id, 'error': str(e), 'retry_count': task.retry_count}
            )
            
            raise e
    
    @staticmethod
    def run_due_tasks():
        """Exécute les tâches dont l'exécution est due."""
        from .models import ScheduledTask
        
        due_tasks = ScheduledTask.objects.filter(
            is_enabled=True,
            next_run__lte=timezone.now(),
            status='active'
        )
        
        results = []
        for task in due_tasks:
            try:
                result = TaskScheduler.execute_task(task)
                task.next_run = TaskScheduler.calculate_next_run(task.schedule)
                task.save()
                results.append({'task': task.name, 'status': 'success', 'result': result})
            except Exception as e:
                results.append({'task': task.name, 'status': 'failed', 'error': str(e)})
        
        return results


class BackupService:
    """Service de sauvegarde."""
    
    @staticmethod
    def create_backup(backup_type='database', include_files=False):
        """Crée une sauvegarde."""
        import tempfile
        import shutil
        from django.core.management import call_command
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{backup_type}_{timestamp}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, backup_name)
            
            if backup_type == 'database':
                # Sauvegarde de la base de données
                db_file = f"{backup_path}.json"
                with open(db_file, 'w') as f:
                    call_command('dumpdata', stdout=f)
                
                # Compression
                shutil.make_archive(backup_path, 'zip', temp_dir, backup_name)
                final_file = f"{backup_path}.zip"
            
            elif backup_type == 'files':
                # Sauvegarde des fichiers média
                if include_files and hasattr(settings, 'MEDIA_ROOT'):
                    media_backup = f"{backup_path}_media"
                    shutil.copytree(settings.MEDIA_ROOT, media_backup)
                    final_file = f"{backup_path}.zip"
                    shutil.make_archive(backup_path, 'zip', temp_dir, backup_name)
            
            else:
                raise ValueError(f"Type de sauvegarde inconnu: {backup_type}")
            
            # Déplacer vers le répertoire de sauvegarde
            backup_dir = getattr(settings, 'BACKUP_DIR', '/var/backups')
            os.makedirs(backup_dir, exist_ok=True)
            final_destination = os.path.join(backup_dir, os.path.basename(final_file))
            shutil.move(final_file, final_destination)
            
            # Log
            LoggingService.info(
                'system',
                'backup',
                'backup_created',
                f"Sauvegarde créée: {backup_type}",
                details={
                    'filename': os.path.basename(final_destination),
                    'size_bytes': os.path.getsize(final_destination)
                }
            )
            
            return final_destination
    
    @staticmethod
    def list_backups():
        """Liste les sauvegardes disponibles."""
        backup_dir = getattr(settings, 'BACKUP_DIR', '/var/backups')
        
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_') and filename.endswith('.zip'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'name': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)


class SecurityService:
    """Service de sécurité."""
    
    @staticmethod
    def check_security():
        """Vérifie la sécurité du système."""
        issues = []
        
        # Vérifier les configurations de sécurité
        if settings.DEBUG:
            issues.append({
                'level': 'high',
                'message': 'Mode DEBUG activé en production',
                'recommendation': 'Désactiver DEBUG dans les settings'
            })
        
        # Vérifier les clés secrètes
        if settings.SECRET_KEY == 'django-insecure-':
            issues.append({
                'level': 'critical',
                'message': 'Clé secrète par défaut utilisée',
                'recommendation': 'Générer une nouvelle clé SECRET_KEY'
            })
        
        # Vérifier les permissions de fichiers
        important_files = [
            settings.BASE_DIR / 'manage.py',
            settings.BASE_DIR / 'requirements.txt',
            settings.BASE_DIR / '.env',
        ]
        
        for file in important_files:
            if file.exists():
                mode = oct(file.stat().st_mode)[-3:]
                if mode != '600' and 'env' in str(file):
                    issues.append({
                        'level': 'medium',
                        'message': f'Permissions trop permissives pour {file.name}',
                        'recommendation': f'Changer les permissions à 600: chmod 600 {file}'
                    })
        
        # Vérifier les mises à jour (simulation)
        issues.append({
            'level': 'info',
            'message': 'Vérifiez régulièrement les mises à jour de sécurité',
            'recommendation': 'Visitez https://docs.djangoproject.com/fr/stable/releases/security/'
        })
        
        return issues
    
    @staticmethod
    def generate_password(length=16):
        """Génère un mot de passe sécurisé."""
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password):
        """Hash un mot de passe."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{salt}{password}".encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    @staticmethod
    def verify_password(password, hashed):
        """Vérifie un mot de passe hashé."""
        try:
            salt, stored_hash = hashed.split(':')
            hash_obj = hashlib.sha256()
            hash_obj.update(f"{salt}{password}".encode())
            return hash_obj.hexdigest() == stored_hash
        except:
            return False