import logging

class AuditLogger:

    @staticmethod
    def log_security_event(user=None, action='', ip_address=None, user_agent=None, details=None):
        """
        Logger centralisé pour les événements de sécurité.
        `user` peut être None pour les échecs d'authentification.
        `details` peut contenir des infos supplémentaires comme 'reason', 'success', etc.
        """
        logger = logging.getLogger('security')
        try:
            logger.info({
                "user_id": getattr(user, 'id', None) if user else None,
                "username": getattr(user, 'username', None) if user else details.get('username') if details else None,
                "action": action,
                "ip_address": str(ip_address) if ip_address else None,
                "user_agent": str(user_agent) if user_agent else None,
                "details": details if details else None,
            })
        except Exception as e:
            logger.error(f"Erreur de logging: {e}")

    @staticmethod
    def log_login_attempt(user=None, username=None, ip_address=None, user_agent=None, success=False, reason=None):
        """
        Logger spécifique pour les tentatives de login.
        `user` peut être None si l'utilisateur n'existe pas.
        """
        details = {
            "success": success,
            "reason": reason
        }
        if username:
            details['username'] = username

        AuditLogger.log_security_event(
            user=user,
            action="login_attempt",
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
