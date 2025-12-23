import logging
import json
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        logger.error(f"API Error: {exception}", exc_info=True)
        
        # Retourner une réponse d'erreur standardisée
        return Response({
            'error': 'Une erreur est survenue',
            'detail': str(exception),
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)