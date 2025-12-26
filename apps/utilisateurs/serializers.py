from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import re
import hashlib
import secrets
import string
from datetime import timedelta, datetime
from .models import VerificationVerificationtoken

User = get_user_model()

# ==================== VALIDATEURS DE SÉCURITÉ ====================

BANNED_PASSWORDS = [
    'password123', '12345678', 'azerty123', 'qwerty123',
    'notairesbf', 'notaires2024', 'admin123', 'user123'
]

class PasswordStrengthValidator:
    """Validateur de force du mot de passe"""
    
    @staticmethod
    def validate(password, user=None):
        errors = []
        
        if len(password) < 12:
            errors.append("Le mot de passe doit contenir au moins 12 caractères.")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Le mot de passe doit contenir au moins une majuscule.")
        
        if not re.search(r'[a-z]', password):
            errors.append("Le mot de passe doit contenir au moins une minuscule.")
        
        if not re.search(r'[0-9]', password):
            errors.append("Le mot de passe doit contenir au moins un chiffre.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial.")
        
        if password.lower() in [p.lower() for p in BANNED_PASSWORDS]:
            errors.append("Ce mot de passe est trop commun.")
        
        if re.search(r'(.)\1{3,}', password):
            errors.append("Trop de caractères identiques consécutifs.")
        
        common_sequences = ['123456', 'abcdef', 'qwerty', 'azerty']
        for seq in common_sequences:
            if seq in password.lower():
                errors.append("Le mot de passe contient une séquence trop commune.")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        password_validation.validate_password(password, user)

class TelephoneValidator:
    """Validateur strict de numéro de téléphone"""
    
    @staticmethod
    def validate(telephone):
        # Nettoyer le numéro
        cleaned = re.sub(r'[\s\-\(\)\+]', '', telephone)
        
        if not cleaned.isdigit():
            raise serializers.ValidationError("Le numéro doit contenir uniquement des chiffres.")
        
        if len(cleaned) not in [8, 9, 10]:
            raise serializers.ValidationError("Numéro de téléphone invalide.")
        
        if len(cleaned) in [8, 9]:
            formatted = f"+226{cleaned}"
        else:
            if cleaned.startswith('226'):
                formatted = f"+{cleaned}"
            else:
                raise serializers.ValidationError("Indicatif pays invalide.")
        
        return formatted

# ==================== GÉNÉRATEUR DE TOKENS ====================

class VerificationTokenGenerator:
    @staticmethod
    def generate_token(length=32):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_otp(length=6):
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def verify_token(stored_hash, provided_token):
        return stored_hash == hashlib.sha256(provided_token.encode()).hexdigest()

# ==================== SÉRIALISEURS PRINCIPAUX ====================

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=False,
        validators=[PasswordStrengthValidator.validate]
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'nom', 'prenom', 'telephone',
            'email_verifie', 'telephone_verifie',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'updated_at'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'updated_at',
            'email_verifie', 'telephone_verifie',
            'is_active', 'is_staff', 'is_superuser'
        ]
    
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Format d'email invalide.")
        return value
    
    def validate_telephone(self, value):
        return TelephoneValidator.validate(value)
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        if password:
            old_password = self.context.get('request').data.get('old_password')
            if not old_password or not instance.check_password(old_password):
                raise serializers.ValidationError({
                    "old_password": "L'ancien mot de passe est incorrect."
                })
            
            if instance.check_password(password):
                raise serializers.ValidationError({
                    "password": "Le nouveau mot de passe doit être différent de l'ancien."
                })
            
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[PasswordStrengthValidator.validate]
    )
    password_confirmation = serializers.CharField(write_only=True)
    accept_terms = serializers.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'nom', 'prenom', 'telephone', 'accept_terms'
        ]
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate_accept_terms(self, value):
        if not value:
            raise serializers.ValidationError("Vous devez accepter les conditions d'utilisation.")
        return value
    
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Email invalide.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        
        reserved_usernames = ['admin', 'root', 'superuser', 'system']
        if value.lower() in reserved_usernames:
            raise serializers.ValidationError("Ce nom d'utilisateur est réservé.")
        
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        
        # Vérifier que le mot de passe ne contient pas d'informations personnelles
        user_info = [
            data.get('nom', '').lower(),
            data.get('prenom', '').lower(),
            data.get('username', '').lower(),
            data.get('email', '').split('@')[0].lower()
        ]
        
        password_lower = data['password'].lower()
        for info in user_info:
            if info and info in password_lower and len(info) > 2:
                raise serializers.ValidationError({
                    "password": "Le mot de passe ne doit pas contenir vos informations personnelles."
                })
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        validated_data.pop('accept_terms')
        
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False  # Désactivé jusqu'à vérification email
        user.save()
        
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'nom', 'prenom', 'telephone',
            'email_verifie', 'telephone_verifie',
            'date_joined'
        ]

# ==================== SÉRIALISEURS DE VÉRIFICATION ====================

class SendVerificationSerializer(serializers.Serializer):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    verification_type = serializers.ChoiceField(choices=TYPE_CHOICES)
    email = serializers.EmailField(required=False)
    telephone = serializers.CharField(required=False)
    
    def validate(self, data):
        verification_type = data['verification_type']
        
        if verification_type == 'email' and not data.get('email'):
            raise serializers.ValidationError({
                "email": "L'email est requis pour la vérification par email"
            })
        
        if verification_type == 'sms' and not data.get('telephone'):
            raise serializers.ValidationError({
                "telephone": "Le téléphone est requis pour la vérification par SMS"
            })
        
        # Rate limiting par IP
        request = self.context.get('request')
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            cache_key = f"verification_send_{ip_address}"
            attempts = cache.get(cache_key, [])
            
            current_time = timezone.now()
            attempts = [t for t in attempts if current_time - t < timedelta(hours=1)]
            
            if len(attempts) >= 10:
                raise serializers.ValidationError({
                    "rate_limit": "Trop de tentatives. Veuillez réessayer dans 1 heure."
                })
            
            attempts.append(current_time)
            cache.set(cache_key, attempts, 3600)
        
        return data
    
    def create(self, validated_data):
        verification_type = validated_data['verification_type']
        email = validated_data.get('email')
        telephone = validated_data.get('telephone')
        request = self.context.get('request')
        
        # Trouver l'utilisateur
        user = None
        if verification_type == 'email':
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Ne pas révéler que l'utilisateur n'existe pas
                return {"message": "Si l'email existe, un code de vérification a été envoyé"}
        else:
            try:
                user = User.objects.get(telephone=telephone)
            except User.DoesNotExist:
                return {"message": "Si le téléphone existe, un code de vérification a été envoyé"}
        
        if not user:
            return {"message": "Si l'email/téléphone existe, un code de vérification a été envoyé"}
        
        # Générer un token OTP
        token = VerificationTokenGenerator.generate_otp(6)
        token_hash = VerificationTokenGenerator.hash_token(token)
        
        # Supprimer les anciens tokens non utilisés
        VerificationVerificationtoken.objects.filter(
            user=user,
            type_token=verification_type,
            used=False,
            expires_at__lt=timezone.now()
        ).delete()
        
        # Créer le nouveau token
        verification_token = VerificationVerificationtoken.objects.create(
            user=user,
            token=token_hash,
            type_token=verification_type,
            expires_at=timezone.now() + timedelta(minutes=15),
            data={
                'ip_address': request.META.get('REMOTE_ADDR') if request else None,
                'user_agent': request.META.get('HTTP_USER_AGENT') if request else None,
                'sent_at': timezone.now().isoformat()
            }
        )
        
        # Envoyer le token
        if verification_type == 'email':
            self._send_email_verification(user, token, email)
        else:
            self._send_sms_verification(user, token, telephone)
        
        return {
            "message": "Un code de vérification a été envoyé",
            "token_id": verification_token.id,
            "expires_at": verification_token.expires_at
        }
    
    def _send_email_verification(self, user, token, email):
        """Envoyer un email de vérification"""
        from django.core.mail import send_mail
        
        subject = f"Code de vérification - Ordre des Notaires BF"
        message = f"""
        Bonjour {user.nom} {user.prenom},
        
        Votre code de vérification est : {token}
        
        Ce code expirera dans 15 minutes.
        
        Si vous n'avez pas demandé cette vérification, veuillez ignorer cet email.
        
        Cordialement,
        L'équipe de l'Ordre des Notaires du Burkina Faso
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur d'envoi d'email: {e}")
    
    def _send_sms_verification(self, user, token, telephone):
        """Envoyer un SMS de vérification"""
        print(f"SMS envoyé à {telephone}: Code de vérification: {token}")
        # TODO: Implémenter avec votre API SMS

class VerifyTokenSerializer(serializers.Serializer):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    token = serializers.CharField(min_length=6, max_length=6)
    verification_type = serializers.ChoiceField(choices=TYPE_CHOICES)
    email = serializers.EmailField(required=False)
    telephone = serializers.CharField(required=False)
    token_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        token = data['token']
        verification_type = data['verification_type']
        email = data.get('email')
        telephone = data.get('telephone')
        token_id = data.get('token_id')
        
        # Rate limiting
        request = self.context.get('request')
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            cache_key = f"verification_attempt_{ip_address}_{token}"
            attempts = cache.get(cache_key, 0)
            
            if attempts >= 5:
                raise serializers.ValidationError({
                    "rate_limit": "Trop de tentatives échouées. Veuillez demander un nouveau code."
                })
        
        # Trouver l'utilisateur
        user = None
        if verification_type == 'email':
            if not email:
                raise serializers.ValidationError({"email": "L'email est requis"})
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError({"token": "Code invalide"})
        else:
            if not telephone:
                raise serializers.ValidationError({"telephone": "Le téléphone est requis"})
            try:
                user = User.objects.get(telephone=telephone)
            except User.DoesNotExist:
                raise serializers.ValidationError({"token": "Code invalide"})
        
        # Chercher le token
        verification_tokens = VerificationVerificationtoken.objects.filter(
            user=user,
            type_token=verification_type,
            used=False,
            expires_at__gt=timezone.now()
        )
        
        if token_id:
            verification_tokens = verification_tokens.filter(id=token_id)
        
        verification_token = None
        for vt in verification_tokens:
            if VerificationTokenGenerator.verify_token(vt.token, token):
                verification_token = vt
                break
        
        if not verification_token:
            # Incrémenter le compteur d'échecs
            if request:
                cache_key = f"verification_attempt_{ip_address}_{token}"
                cache.set(cache_key, attempts + 1, 300)
            raise serializers.ValidationError({"token": "Code invalide ou expiré"})
        
        data['user'] = user
        data['verification_token'] = verification_token
        return data
    
    def create(self, validated_data):
        user = validated_data['user']
        verification_token = validated_data['verification_token']
        verification_type = validated_data['verification_type']
        
        # Marquer le token comme utilisé
        verification_token.used = True
        verification_token.save()
        
        # Mettre à jour l'utilisateur
        if verification_type == 'email':
            user.email_verifie = True
        else:
            user.telephone_verifie = True
        
        # Activer le compte si l'email est vérifié
        if verification_type == 'email' and not user.is_active:
            user.is_active = True
        
        user.save()
        
        # Nettoyer les tokens expirés
        VerificationVerificationtoken.objects.filter(
            user=user,
            type_token=verification_type,
            used=False,
            expires_at__lt=timezone.now()
        ).delete()
        
        return {
            "success": True,
            "message": f"{verification_type.capitalize()} vérifié avec succès",
            "user_id": user.id
        }

class VerificationTokenSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = VerificationVerificationtoken
        fields = [
            'id', 'user', 'user_details', 'token', 'type_token',
            'expires_at', 'used', 'data',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# ==================== SÉRIALISEURS SUPPLÉMENTAIRES ====================

class ResendVerificationSerializer(serializers.Serializer):
    verification_type = serializers.ChoiceField(
        choices=[('email', 'Email'), ('sms', 'SMS')]
    )
    identifier = serializers.CharField(required=True)
    
    def validate(self, data):
        verification_type = data['verification_type']
        identifier = data['identifier']
        
        # Rate limiting pour les renvois
        request = self.context.get('request')
        ip_address = request.META.get('REMOTE_ADDR') if request else None
        
        cache_key = f"resend_verification_{ip_address}_{identifier}"
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 3:
            raise serializers.ValidationError({
                "rate_limit": "Trop de demandes de renvoi. Veuillez patienter."
            })
        
        # Vérifier que l'utilisateur existe
        user = None
        if verification_type == 'email':
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(telephone=identifier)
            except User.DoesNotExist:
                pass
        
        if not user:
            # Incrementer quand même pour éviter l'énumération
            cache.set(cache_key, attempts + 1, 3600)
            return data
        
        # Invalider les anciens tokens
        VerificationVerificationtoken.objects.filter(
            user=user,
            type_token=verification_type,
            used=False,
            expires_at__gt=timezone.now()
        ).update(used=True)
        
        data['user'] = user
        cache.set(cache_key, attempts + 1, 3600)
        
        return data
    
    def create(self, validated_data):
        user = validated_data.get('user')
        verification_type = validated_data['verification_type']
        identifier = validated_data['identifier']
        
        if not user:
            # Pour éviter l'énumération
            return {
                "message": "Si l'identifiant existe, un nouveau code a été envoyé",
                "next_action": "check_identifier"
            }
        
        # Générer un nouveau token
        token = VerificationTokenGenerator.generate_otp(6)
        token_hash = VerificationTokenGenerator.hash_token(token)
        
        # Créer le nouveau token
        verification_token = VerificationVerificationtoken.objects.create(
            user=user,
            token=token_hash,
            type_token=verification_type,
            expires_at=timezone.now() + timedelta(minutes=15),
            data={'is_resend': True}
        )
        
        # Envoyer le token
        if verification_type == 'email':
            from django.core.mail import send_mail
            
            subject = f"Nouveau code de vérification - Ordre des Notaires BF"
            message = f"""
            Bonjour {user.nom} {user.prenom},
            
            Votre nouveau code de vérification est : {token}
            
            Ce code expirera dans 15 minutes.
            
            Cordialement,
            L'équipe de l'Ordre des Notaires du Burkina Faso
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [identifier],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Erreur d'envoi d'email: {e}")
        else:
            print(f"Nouveau SMS envoyé à {identifier}: Code: {token}")
            # TODO: Implémenter avec votre API SMS
        
        return {
            "message": "Un nouveau code de vérification a été envoyé",
            "token_id": verification_token.id,
            "expires_at": verification_token.expires_at,
            "verification_type": verification_type
        }

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, 
        required=True,
        validators=[PasswordStrengthValidator.validate]
    )
    new_password_confirmation = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirmation']:
            raise serializers.ValidationError({
                "new_password": "Les nouveaux mots de passe ne correspondent pas."
            })
        
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({
                "new_password": "Le nouveau mot de passe doit être différent de l'ancien."
            })
        
        return data

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Email invalide.")
        return value
    
"""
    creation d'un administrateur (réservé aux superutilisateurs)

class AdminCreateSerializer(serializers.ModelSerializer):
    'sérialiseur pour créer un administrateur (réservé aux superutilisateurs)'
    password = serializers.CharField(
        write_only=True,
        validators=[PasswordStrengthValidator.validate],
        min_length=12
    )
    password_confirmation = serializers.CharField(write_only=True, min_length=12)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'nom', 'prenom', 'telephone',
            'is_staff', 'is_superuser'
        ]
    
    def validate(self, data):
        # Validation de base
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        
        # Vérifier les permissions de l'utilisateur qui fait la requête
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            # Empêcher un non-superutilisateur de créer un superutilisateur
            if data.get('is_superuser', False) or data.get('is_staff', False):
                raise serializers.ValidationError({
                    "permission": "Vous n'avez pas la permission de créer un administrateur."
                })
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        
        # Créer l'utilisateur avec les permissions
        user = User.objects.create(**validated_data)
        user.set_password(password)
        
        # Si c'est un superutilisateur, activer automatiquement
        if user.is_superuser:
            user.is_active = True
            user.email_verifie = True
        
        user.save()
        return user
"""