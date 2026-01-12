from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import Throttled
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.core.cache import cache
from .models import VerificationVerificationtoken
from .serializers import (
    UserSerializer, UserCreateSerializer, UserProfileSerializer,
    SendVerificationSerializer, VerifyTokenSerializer,
    PasswordResetSerializer, PasswordChangeSerializer,
    AdminCreateSerializer,
    ResendVerificationSerializer,
    LoginSerializer,
)
from .security.rate_limiter import LoginRateLimiter
from .security.audit_logger import AuditLogger
from .permissions import IsSuperUser, IsAdminUser, IsOwnerOrAdmin
#from .serializers import AdminCreateSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Mettre à jour le profil de l'utilisateur connecté"""
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouvel utilisateur"""
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Inscription réussie. Un code de vérification a été envoyé par SMS à votre numéro de téléphone.',
            'user_id': user.id,
            'telephone': user.telephone,
            'next_step': 'verify_telephone'
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    """
    Authentification JWT sécurisée
    - Validation serializer
    - Rate limiting
    - Audit logging
    - Support 2FA
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        # 1️⃣ Validation des données
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        # 2️⃣ Rate limiting (avant authentification)
        try:
            LoginRateLimiter.check_login_attempt(ip_address)
            LoginRateLimiter.check_login_attempt(username)
        except Throttled:
            AuditLogger.log_login_attempt(
                username=username,
                ip_address=ip_address,
                success=False,
                reason="rate_limited",
                user_agent=user_agent
            )
            raise

        # 3️⃣ Authentification
        user = authenticate(
            request=request,
            username=username,
            password=password
        )

        if not user:
            # L'incrémentation a déjà été faite par check_login_attempt() au début
            AuditLogger.log_login_attempt(
                username=username,
                ip_address=ip_address,
                success=False,
                reason="invalid_credentials",
                user_agent=user_agent
            )

            return Response(
                {"error": "Identifiants invalides"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 4️⃣ Vérifications de sécurité
        if not user.is_active:
            return Response(
                {"error": "Accès refusé"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not getattr(user, 'email_verifie', True):
            return Response(
                {"error": "Vérification requise"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 5️⃣ 2FA si activé
        if getattr(user, 'two_factor_enabled', False):
            send_serializer = SendVerificationSerializer(
                data={
                    "verification_type": getattr(user, 'two_factor_method', 'email'),
                    "email": user.email if user.two_factor_method == 'email' else None,
                    "telephone": user.telephone if user.two_factor_method == 'sms' else None
                },
                context={"request": request}
            )
            send_serializer.is_valid(raise_exception=True)
            send_serializer.save()

            return Response(
                {
                    "message": "Code de vérification envoyé",
                    "next_step": "verify_2fa"
                },
                status=status.HTTP_200_OK
            )

        # 6️⃣ Succès → génération JWT
        refresh = RefreshToken.for_user(user)

        # Nettoyage rate limit
        LoginRateLimiter.clear_attempts(ip_address)
        LoginRateLimiter.clear_attempts(username)

        # Audit succès
        AuditLogger.log_login_attempt(
            user=user,
            ip_address=ip_address,
            success=True,
            user_agent=user_agent
        )

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserProfileSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

class SendVerificationView(generics.CreateAPIView):
    """Envoyer un code de vérification"""
    serializer_class = SendVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

class VerifyTokenView(generics.CreateAPIView):
    """Vérifier un code de vérification"""
    serializer_class = VerifyTokenSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        # Si c'est une vérification d'email après inscription, activer le compte
        if result.get('user_id'):
            user = User.objects.get(id=result['user_id'])
            if not user.is_active and user.email_verifie:
                user.is_active = True
                user.save()
                
                # Générer des tokens JWT
                refresh = RefreshToken.for_user(user)
                result.update({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserProfileSerializer(user).data
                })
        
        return Response(result, status=status.HTTP_200_OK)

class ResendVerificationView(generics.CreateAPIView):
    """Renvoyer un code de vérification"""
    serializer_class = ResendVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response(result, status=status.HTTP_200_OK)

class PasswordResetView(generics.CreateAPIView):
    """Demande de réinitialisation de mot de passe"""
    serializer_class = PasswordResetSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # Ici, vous pouvez ajouter la logique d'envoi d'email de réinitialisation
        return Response({
            'message': 'Si votre email existe, vous recevrez un lien de réinitialisation'
        }, status=status.HTTP_200_OK)

class PasswordChangeView(generics.UpdateAPIView):
    """Changer le mot de passe"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Vérifier l'ancien mot de passe
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Ancien mot de passe incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Changer le mot de passe
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({
            'message': 'Mot de passe changé avec succès'
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """Déconnexion en blacklistant le refresh token"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # nécessite l'app token_blacklist activée
            return Response({"message": "Déconnecté avec succès"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


"""
Vue creation et gestion des administrateurs
"""

class AdminCreateView(generics.CreateAPIView):
    """Créer un administrateur"""
    serializer_class = AdminCreateSerializer

    def get_permissions(self):
        # Si aucun superuser n'existe, autoriser la création
        if not User.objects.filter(is_superuser=True).exists():
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]  # Autorise utilisateurs authentifiés

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Créer l'utilisateur avec is_active=False (nécessite vérification OTP)
        user = serializer.save(is_active=False)

        # Générer et envoyer le code de vérification par SMS
        from .serializers import SendVerificationSerializer
        from apps.communications.services import SMSService

        try:
            # Créer directement le token OTP pour ce nouvel utilisateur
            from .models import VerificationVerificationtoken
            from .serializers import VerificationTokenGenerator
            import logging

            # Générer le token
            token = VerificationTokenGenerator.generate_otp(6)
            token_hash = VerificationTokenGenerator.hash_token(token)

            # Créer le token en base
            VerificationVerificationtoken.objects.create(
                user=user,
                token=token_hash,  # Stocker le hash du token
                type_token='sms',  # Doit correspondre aux choix du serializer
                expires_at=timezone.now() + timezone.timedelta(minutes=10),
                data={'purpose': 'admin_creation', 'original_token': token}  # Debug: garder le token original dans data
            )

            # Envoyer le SMS
            from apps.communications.services import SMSService
            SMSService.send_verification_sms(user.telephone, token, f"{user.nom} {user.prenom}")

        except Exception as e:
            # En cas d'erreur SMS, logger mais ne pas bloquer la création
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur envoi SMS pour admin {user.username}: {str(e)}")
            # On continue quand même la création

        return Response({
            'message': 'Administrateur créé. Un code de vérification a été envoyé par SMS.',
            'user_id': user.id,
            'telephone': user.telephone,
            'verification_required': True
        }, status=status.HTTP_201_CREATED)


class AdminManagementViewSet(viewsets.ModelViewSet):
    #Gestion des administrateurs (CRUD complet)
    serializer_class = UserSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        # Filtrer pour ne montrer que les utilisateurs avec des privilèges
        return User.objects.filter(is_staff=True)

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]  # Autorise utilisateurs authentifiés
        return [IsSuperUser()]  # Garde sécurité pour autres actions
    @action(detail=True, methods=['post'])
    def grant_admin(self, request, pk=None):
      #  Donner les droits d'administrateur à un utilisateur
        user = self.get_object()
        user.is_staff = True
        user.save()
        
        # Journaliser l'action
        AuditLogger.log_security_event(
            user=request.user,
            action='grant_admin',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={'target_user_id': user.id, 'target_username': user.username}
        )
        
        return Response({
            'message': f'Droits administrateur accordés à {user.username}',
            'user_id': user.id,
            'is_staff': user.is_staff
        })

    @action(detail=True, methods=['post'])
    def verify_admin_otp(self, request, pk=None):
        """Vérifier l'OTP et activer un compte admin nouvellement créé"""
        user = self.get_object()

        # Logging pour debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Vérification OTP pour admin {user.username} (ID: {user.id})")

        # Vérifier que l'utilisateur n'est pas encore actif
        if user.is_active:
            logger.warning(f"Tentative de vérification OTP pour compte déjà actif: {user.username}")
            return Response({
                'error': 'Ce compte est déjà actif'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier l'OTP
        from .serializers import VerifyTokenSerializer
        token_data = request.data.copy()
        token_data['telephone'] = user.telephone

        logger.info(f"Données de vérification: telephone={user.telephone}, token fourni")

        try:
            serializer = VerifyTokenSerializer(
                data=token_data,
                context={'request': request}
            )

            # Validation avec gestion d'erreur détaillée
            if not serializer.is_valid():
                logger.error(f"Erreur de validation OTP: {serializer.errors}")
                return Response({
                    'error': 'Données de vérification invalides',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            result = serializer.save()
            logger.info(f"Résultat de vérification OTP: {result}")

            # Activer le compte si la vérification réussit
            if result.get('verified', False):
                user.is_active = True
                user.save()

                # Générer les tokens JWT
                refresh = RefreshToken.for_user(user)

            # Journaliser l'activation
            AuditLogger.log_security_event(
                user=request.user,
                action='activate_admin_account',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={'target_user_id': user.id, 'target_username': user.username}
            )

            return Response({
                'message': 'Compte administrateur activé avec succès',
                'user_id': user.id,
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la vérification OTP: {str(e)}")
            return Response({
                'error': 'Erreur interne du serveur',
                'details': str(e) if settings.DEBUG else 'Contactez l\'administrateur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'error': 'Code de vérification invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def revoke_admin(self, request, pk=None):
       # Retirer les droits d'administrateur d'un utilisateur
        user = self.get_object()
        
        # Empêcher de se retirer soi-même les droits
        if user == request.user:
            return Response({
                'error': 'Vous ne pouvez pas vous retirer vos propres droits administrateur'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_staff = False
        user.is_superuser = False
        user.save()
        
        # Journaliser l'action
        AuditLogger.log_security_event(
            user=request.user,
            action='revoke_admin',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={'target_user_id': user.id, 'target_username': user.username}
        )
        
        return Response({
            'message': f'Droits administrateur retirés à {user.username}',
            'user_id': user.id,
            'is_staff': user.is_staff
        })


