import logging
import json
import traceback
from django.conf import settings
from django.http import JsonResponse, HttpResponseServerError
from django.urls import resolve, Resolver404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

class JWTTokenRefreshMiddleware:
    """
    Middleware pour gérer automatiquement le rafraîchissement des tokens JWT expirés.
    Intercepte les erreurs de token expiré et tente de les rafraîchir automatiquement.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Vérifier si c'est une erreur de token expiré
        if (response.status_code == 401 and
            hasattr(response, 'data') and
            isinstance(response.data, dict) and
            response.data.get('code') == 'token_not_valid'):

            # Tenter de rafraîchir automatiquement le token
            refresh_response = self._try_refresh_token(request)
            if refresh_response:
                return refresh_response

        return response

    def _try_refresh_token(self, request):
        """
        Tente de rafraîchir le token en utilisant le refresh token dans les cookies ou headers
        """
        try:
            # Chercher le refresh token dans les cookies
            refresh_token = request.COOKIES.get('refresh_token')

            # Ou dans l'Authorization header (format: Bearer <access_token> <refresh_token>)
            if not refresh_token:
                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                if auth_header.startswith('Bearer '):
                    parts = auth_header.split()
                    if len(parts) >= 3:
                        refresh_token = parts[2]  # Le refresh token serait en 3ème position

            if refresh_token:
                # Valider et utiliser le refresh token
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)

                # Créer une nouvelle réponse avec le nouveau token
                return JsonResponse({
                    'detail': 'Token rafraîchi automatiquement',
                    'access': new_access_token,
                    'refresh': str(refresh) if settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] else refresh_token
                }, status=200)

        except (TokenError, InvalidToken) as e:
            logger.warning(f"Échec du rafraîchissement automatique du token: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement automatique: {str(e)}")

        return None


class ExceptionMiddleware:
    """
    Middleware amélioré pour gérer les exceptions de manière sécurisée.
    Distingue les API REST des pages HTML et ne leak pas d'informations sensibles.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Gère les exceptions de manière sécurisée selon le type de requête.
        """
        # Logger l'erreur avec le contexte complet
        self._log_exception(request, exception)

        # Déterminer si c'est une requête API
        is_api_request = self._is_api_request(request)

        if is_api_request:
            return self._handle_api_exception(request, exception)
        else:
            return self._handle_html_exception(request, exception)

    def _log_exception(self, request, exception):
        """Log l'exception avec contexte détaillé"""
        try:
            user = getattr(request, 'user', None)
            user_info = f"User: {user.username if user and user.is_authenticated else 'Anonymous'}"
        except:
            user_info = "User: Unknown"

        logger.error(
            f"Exception in {request.method} {request.path} - {user_info}",
            exc_info=True,
            extra={
                'request_method': request.method,
                'request_path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'remote_addr': self._get_client_ip(request),
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
            }
        )

    def _is_api_request(self, request):
        """Détermine si la requête concerne l'API"""
        path = request.path_info

        # Vérifier si le chemin commence par /api/
        if path.startswith('/api/'):
            return True

        # Vérifier le Content-Type pour les requêtes AJAX
        content_type = request.META.get('CONTENT_TYPE', '')
        accept = request.META.get('HTTP_ACCEPT', '')

        if 'application/json' in content_type or 'application/json' in accept:
            return True

        # Vérifier si c'est une requête AJAX
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return True

        return False

    def _handle_api_exception(self, request, exception):
        """Gère les exceptions pour les requêtes API"""

        # Gestion spécifique des exceptions DRF
        if isinstance(exception, APIException):
            return Response({
                'error': 'Erreur de validation',
                'detail': str(exception.detail) if hasattr(exception, 'detail') else str(exception),
                'status_code': exception.status_code
            }, status=exception.status_code)

        # Gestion des erreurs de base de données
        if 'database' in str(type(exception)).lower():
            return Response({
                'error': 'Erreur de base de données',
                'detail': 'Une erreur temporaire est survenue. Veuillez réessayer.',
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Erreur générique pour l'API (pas de détails sensibles)
        error_detail = 'Une erreur inattendue est survenue.'

        # En développement, on peut montrer plus de détails
        if settings.DEBUG:
            error_detail = str(exception)

        return Response({
            'error': 'Erreur interne du serveur',
            'detail': error_detail,
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_html_exception(self, request, exception):
        """Gère les exceptions pour les pages HTML"""
        # Pour les pages HTML, on laisse Django gérer avec ses vues d'erreur par défaut
        # ou on peut rediriger vers une page d'erreur personnalisée
        return None  # Laisser Django gérer

    def _get_client_ip(self, request):
        """Récupère l'adresse IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip