from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    RegisterView,
    LoginView,
    SendVerificationView,
    VerifyTokenView,
    ResendVerificationView,
    PasswordResetView,
    PasswordChangeView,
    AdminCreateView,
    AdminManagementViewSet
)

# Routeur pour la gestion des administrateurs
admin_router = DefaultRouter()
admin_router.register(r'admins', AdminManagementViewSet, basename='admin')

urlpatterns = [
    # URLs publiques
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('send-verification/', SendVerificationView.as_view(), name='send-verification'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('password/reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    
    # URLs utilisateurs (authentifiés)
    path('users/', include([
        path('', UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
        path('<int:pk>/', UserViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), name='user-detail'),
        path('me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
        path('update-profile/', UserViewSet.as_view({'put': 'update_profile', 'patch': 'update_profile'}), name='update-profile'),
    ])),
    
    # URLs administrateurs (superutilisateurs uniquement)
    path('admin/create/', AdminCreateView.as_view(), name='admin-create'),
    path('admin/', include(admin_router.urls)),
]