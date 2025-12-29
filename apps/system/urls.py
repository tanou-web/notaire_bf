# apps/system/urls.py - VERSION AVEC PRÉFIXE "api/" DANS NOTAIRES_BF/URLS.PY
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from . import views

# ========================================
# ROUTER
# ========================================

router = DefaultRouter()

# ✅ SEULEMENT la ViewSet qui existe
router.register(r'emails-professionnels', views.SystemEmailprofessionnelViewSet, basename='email-professionnel')

# ========================================
# URL PATTERNS (SANS "api/" ici car déjà dans notaires_bf/urls.py)
# ========================================

urlpatterns = [
    # Routes du router
    path('', include(router.urls)),
    
    # Endpoints supplémentaires
    path('info/', lambda r: JsonResponse({
        'service': 'System API',
        'endpoints': {
            'emails': 'emails-professionnels/',
            'health': 'health/',
            'info': 'info/'
        }
    }), name='system-info'),
    
    path('health/', lambda r: JsonResponse({'status': 'healthy'}), name='system-health'),
    
    path('test/', lambda r: JsonResponse({'message': 'System API working'}), name='system-test'),
]