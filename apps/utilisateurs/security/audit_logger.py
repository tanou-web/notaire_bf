import logging

logger = logging.getLogger('audit')

class AuditLogger:
    """Logger simplifié pour l'audit de sécurité"""
    
    @staticmethod
    def log_login_attempt(username=None, ip_address=None, success=False,
                         user=None, reason=None, user_agent=None):
        """Journalise une tentative de connexion"""
        try:
            # Logging dans les logs système
            user_id = user.id if user else 'anonymous'
            logger.info(
                f"Login Attempt - User ID: {user_id} - "
                f"Username: {username} - IP: {ip_address} - "
                f"Success: {success} - Reason: {reason}"
            )
        except Exception as e:
            logger.error(f"Erreur de journalisation login: {e}")