from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import Throttled
import time
import hashlib

class LoginRateLimiter:
    """Rate limiter spécifique pour les tentatives de login"""
    
    @staticmethod
    def check_login_attempt(identifier, max_attempts=5, window_minutes=15):
        """
        Vérifie et enregistre une tentative de login
        identifier: email/username ou IP
        """
        cache_key = f"login_attempts_{hashlib.md5(identifier.encode()).hexdigest()}"
        now = timezone.now()
        
        attempts = cache.get(cache_key, [])
        
        # Nettoyer les tentatives anciennes
        recent_attempts = [
            attempt_time for attempt_time in attempts 
            if (now - attempt_time).total_seconds() < window_minutes * 60
        ]
        
        if len(recent_attempts) >= max_attempts:
            # Calculer le temps d'attente restant
            oldest_attempt = recent_attempts[0]
            wait_seconds = window_minutes * 60 - (now - oldest_attempt).total_seconds()
            raise Throttled(
                wait=int(wait_seconds),
                detail=f"Trop de tentatives. Réessayez dans {int(wait_seconds)} secondes."
            )
        
        # Ajouter la nouvelle tentative
        recent_attempts.append(now)
        cache.set(cache_key, recent_attempts, window_minutes * 60)
        
        return len(recent_attempts)
    
    @staticmethod
    def clear_attempts(identifier):
        """Efface les tentatives après un login réussi"""
        cache_key = f"login_attempts_{hashlib.md5(identifier.encode()).hexdigest()}"
        cache.delete(cache_key)