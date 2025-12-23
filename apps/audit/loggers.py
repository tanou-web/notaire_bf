import logging
from django.utils import timezone
from .models import SecurityLog, LoginAttemptLog, TokenUsageLog

logger = logging.getLogger('audit')

class AuditLogger:
    """Logger centralisé pour l'audit de sécurité"""
    
    @staticmethod
    def log_security_event(user, action, ip_address=None, 
                          user_agent=None, details=None, status_code=None):
        """Journalise un événement de sécurité"""
        try:
            SecurityLog.objects.create(
                user=user,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else '',
                details=details or {},
                status_code=status_code
            )
            
            # Logging supplémentaire dans les logs système
            logger.info(
                f"Security Event - User: {user.id if user else 'Anonymous'} - "
                f"Action: {action} - IP: {ip_address}"
            )
            
        except Exception as e:
            logger.error(f"Erreur de journalisation: {e}")
    
    @staticmethod
    def log_login_attempt(username, ip_address, success=False, 
                         user=None, reason=None, user_agent=None):
        """Journalise une tentative de connexion"""
        try:
            LoginAttemptLog.objects.create(
                user=user,
                username=username,
                ip_address=ip_address,
                success=success,
                failure_reason=reason if not success else None,
                user_agent=user_agent[:500] if user_agent else ''
            )
            
            # Action correspondante dans SecurityLog
            action = 'login_success' if success else 'login_failed'
            AuditLogger.log_security_event(
                user=user,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    'username': username,
                    'failure_reason': reason
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur de journalisation login: {e}")
    
    @staticmethod
    def log_token_usage(user, token_type, action, token_id=None, ip_address=None):
        """Journalise l'utilisation d'un token"""
        try:
            TokenUsageLog.objects.create(
                user=user,
                token_type=token_type,
                action=action,
                token_id=token_id,
                ip_address=ip_address
            )
            
            # Action correspondante dans SecurityLog
            security_action = f"{token_type}_{action}"
            AuditLogger.log_security_event(
                user=user,
                action=security_action,
                ip_address=ip_address,
                details={'token_id': token_id}
            )
            
        except Exception as e:
            logger.error(f"Erreur de journalisation token: {e}")
    
    @staticmethod
    def log_rate_limit(identifier, limit_type, ip_address=None):
        """Journalise le déclenchement d'un rate limit"""
        try:
            AuditLogger.log_security_event(
                user=None,
                action='rate_limit_triggered',
                ip_address=ip_address,
                details={
                    'identifier': identifier,
                    'limit_type': limit_type,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Erreur de journalisation rate limit: {e}")