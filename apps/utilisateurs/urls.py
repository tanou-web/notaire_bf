# apps/utilisateurs/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LoginView, UserViewSet, LogoutView
from .views import (
    LoginView, LogoutView, RegisterView, SendVerificationView,
    VerifyTokenView, ResendVerificationView,
    PasswordResetView, PasswordChangeView,
    AdminCreateView, AdminManagementViewSet
)
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'admins', AdminManagementViewSet, basename='admin')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),                # Connexion
    path('logout/', LogoutView.as_view(), name='logout'),             # Déconnexion
    path('register/', RegisterView.as_view(), name='register'),       # Inscription
    path('send-verification/', SendVerificationView.as_view(), name='send_verification'),  # Envoi code
    path('verify-token/', VerifyTokenView.as_view(), name='verify_token'),                 # Vérification code
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'), # Renvoyer code
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),           # Réinitialisation mdp
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),        # Changement mdp
    path('create-admin/', AdminCreateView.as_view(), name='create_admin'),                 # Créer un admin (superuser req.)
]


# Inclure le router pour les endpoints CRUD utilisateur
urlpatterns += router.urls
