from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
	SecurityLogViewSet, LoginAttemptLogViewSet,
	TokenUsageLogViewSet, AuditAdminActionViewSet
)

router = DefaultRouter()
router.register(r'security', SecurityLogViewSet, basename='security')
router.register(r'login-attempts', LoginAttemptLogViewSet, basename='loginattempt')
router.register(r'token-usage', TokenUsageLogViewSet, basename='tokenusage')
router.register(r'admin-actions', AuditAdminActionViewSet, basename='adminaction')

urlpatterns = [
	path('', include(router.urls)),
]
