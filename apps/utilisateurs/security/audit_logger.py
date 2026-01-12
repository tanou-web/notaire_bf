import logging

class AuditLogger:

    @staticmethod
    def log_security_event(user, action, ip_address=None, user_agent=None, details=None):
        logger = logging.getLogger('security')
        try:
            logger.info({
                "user_id": getattr(user, 'id', None),
                "username": getattr(user, 'username', None),
                "action": action,
                "ip_address": str(ip_address) if ip_address else None,
                "user_agent": str(user_agent) if user_agent else None,
                "details": str(details) if details else None,
            })
        except Exception as e:
            logger.error(f"Erreur de logging: {e}")
