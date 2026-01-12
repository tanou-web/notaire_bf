from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from datetime import timedelta,datetime
from .models import VerificationVerificationtoken
import hashlib
import string
import secrets
import re
from django.core.mail import send_mail
from apps.communications.services import SMSService


User = get_user_model()
# Liste des mots de passe trop communs
BANNED_PASSWORDS = [
    'password123', '12345678', 'azerty123', 'qwerty123',
    'notairesbf', 'notaires2024', 'admin123', 'user123'
]

class PasswordStrengthValidator:
    """Validateur de force du mot de passe"""
    
    @staticmethod
    def validate(password, user=None):
        errors = []
        
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères.")
        
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

        if len(cleaned) not in [8, 9, 10, 11]:
            raise serializers.ValidationError("Numéro de téléphone invalide.")

        # Format court burkinabè (8 chiffres) : 66342505 → +22666342505
        if len(cleaned) == 8:
            formatted = f"+226{cleaned}"
        # Format avec indicatif local (9 chiffres) : 266342505 → +22666342505
        elif len(cleaned) == 9:
            if cleaned.startswith('26'):
                formatted = f"+{cleaned}"
            else:
                formatted = f"+226{cleaned[1:]}"  # Enlever le premier chiffre si pas 26
        # Format international (10 chiffres) : 22666342505 → +22666342505
        elif len(cleaned) == 10:
            if cleaned.startswith('226'):
                formatted = f"+{cleaned}"
            else:
                raise serializers.ValidationError("Indicatif pays invalide.")
        # Format international avec + (11 chiffres) : +22666342505 → +22666342505
        elif len(cleaned) == 11:
            if cleaned.startswith('226'):
                formatted = f"+{cleaned[1:]}"  # Enlever le + au début
            else:
                raise serializers.ValidationError("Format international invalide.")
        else:
            raise serializers.ValidationError("Numéro de téléphone invalide.")

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
        user = User(**validated_data)
        
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
            'telephone': {'required': True},  # Téléphone obligatoire pour l'envoi de SMS
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
    
    def validate_telephone(self, value):
        """Valider et formater le numéro de téléphone"""
        if not value:
            raise serializers.ValidationError("Le numéro de téléphone est obligatoire.")
        
        # Valider et formater le numéro
        formatted_phone = TelephoneValidator.validate(value)
        
        # Vérifier que le téléphone n'est pas déjà utilisé
        if User.objects.filter(telephone=formatted_phone).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        
        return formatted_phone
    
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
        telephone = validated_data.get('telephone')
        
        # Utiliser une transaction pour s'assurer que si l'envoi SMS échoue,
        # l'utilisateur et le token ne sont pas créés
        with transaction.atomic():
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.is_active = False  # Désactivé jusqu'à vérification du téléphone
            user.save()
            
            # Générer un OTP pour la vérification par SMS
            otp_token = VerificationTokenGenerator.generate_otp(6)
            token_hash = VerificationTokenGenerator.hash_token(otp_token)
            
            # Supprimer les anciens tokens non utilisés pour ce téléphone
            VerificationVerificationtoken.objects.filter(
                user=user,
                type_token='telephone',
                expires_at__lt=timezone.now()
            ).delete()
            
            # Créer le token de vérification
            request = self.context.get('request')
            verification_token = VerificationVerificationtoken.objects.create(
                user=user,
                token=token_hash,
                type_token='telephone',
                expires_at=timezone.now() + timedelta(minutes=15),
                data={
                    'ip_address': request.META.get('REMOTE_ADDR') if request else None,
                    'user_agent': request.META.get('HTTP_USER_AGENT') if request else None,
                    'sent_at': timezone.now().isoformat()
                }
            )
            
            # Envoyer l'OTP par SMS (obligatoire)
            # Si l'envoi échoue, la transaction sera annulée et l'utilisateur ne sera pas créé
            try:
                success, message_id, error = SMSService.send_verification_sms(
                    phone_number=telephone,
                    token=otp_token,
                    user_name=user.get_full_name()
                )
                if not success:
                    # Si l'envoi SMS échoue, on lève une exception pour annuler la transaction
                    # car l'envoi SMS est maintenant obligatoire
                    raise serializers.ValidationError({
                        "telephone": f"Impossible d'envoyer le SMS de vérification. Erreur: {error or 'Erreur inconnue'}"
                    })
            except serializers.ValidationError:
                # Re-lever les ValidationError pour annuler la transaction
                raise
            except Exception as e:
                # Si une exception survient, on lève une erreur de validation
                raise serializers.ValidationError({
                    "telephone": f"Erreur lors de l'envoi du SMS de vérification: {str(e)}"
                })
        
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

            def get_client_ip(request):
                x_frowarded_for = request.META.get('HTTP_XFORWARDED_FOR')
                if x_frowarded_for:
                    return x_frowarded_for.split(',')[0]
                return request.META.get('REMOTE_ADDR')

            ip_address = get_client_ip(request)

            
            cache_key = f"verification_send_{ip_address}"
            attempts = cache.get(cache_key, [])
            
            current_time = timezone.now()
            attempts = [t for t in attempts if current_time - t < timedelta(hours=1)]
            
            if len(attempts) >= 4:
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
            expires_at=timezone.now() + timedelta(minutes=5),
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
        
        subject = f"Code de vérification - Ordre des Notaires BF"
        message = f"""
        Bonjour {user.nom} {user.prenom},
        
        Votre code de vérification est : {token}
        
        Ce code expirera dans 5 minutes.
        
        
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
        try:
            success, message_id, error = SMSService.send_verification_sms(
                phone_number=telephone,
                token=token,
                user_name=user.get_full_name() if user else None
            )
            if not success:
                # Log l'erreur mais ne bloque pas le processus
                print(f"Erreur envoi SMS à {telephone}: {error}")
        except Exception as e:
            print(f"Exception lors de l'envoi SMS à {telephone}: {e}")
            # Ne pas lever d'exception pour ne pas bloquer le processus d'inscription

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
            
            if attempts >= 3:
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

        # Logging détaillé pour debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Recherche tokens pour user={user.username}, type={verification_type}")
        logger.info(f"Tokens trouvés: {verification_tokens.count()}")

        for vt in verification_tokens:
            logger.info(f"Token ID {vt.id}: hash={vt.token[:20]}..., data={vt.data}")

        if token_id:
            verification_tokens = verification_tokens.filter(id=token_id)

        verification_token = None
        for vt in verification_tokens:
            is_valid = VerificationTokenGenerator.verify_token(vt.token, token)
            logger.info(f"Vérification token {vt.id}: fourni='{token}', valide={is_valid}")
            if is_valid:
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
            # Envoyer le SMS de vérification
            try:
                success, message_id, error = SMSService.send_verification_sms(
                    phone_number=identifier,
                    token=token,
                    user_name=f"{user.nom} {user.prenom}" if user else None
                )
                if not success:
                    print(f"Erreur envoi SMS à {identifier}: {error}")
            except Exception as e:
                print(f"Exception lors de l'envoi SMS à {identifier}: {e}")
        
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
"""
class AdminCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer un administrateur (réservé aux superutilisateurs)"""
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
        # Vérifier correspondance des mots de passe
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })

        # Vérifier les permissions du créateur
        request = self.context.get('request')
        first_superuser = not User.objects.filter(is_superuser=True).exists()

        if not first_superuser:
            if request and hasattr(request, 'user') and request.user and not request.user.is_superuser:
                # Empêcher un non-superutilisateur de créer un superuser
                if data.get('is_superuser', False):
                    raise serializers.ValidationError({
                        "permission": "Seul un superutilisateur peut créer un superutilisateur."
                    })
                # Permettre aux utilisateurs authentifiés de créer des admins staff
                elif data.get('is_staff', False):
                    # Autoriser la création d'admin staff pour les utilisateurs authentifiés
                    pass

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')

        # Détecter si c'est le premier utilisateur
        first_superuser = not User.objects.filter(is_superuser=True).exists()
        if first_superuser:
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
            # NE PAS forcer is_active=True pour permettre l'OTP
            validated_data['email_verifie'] = True

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour l'authentification utilisateur
    """
    username = serializers.CharField(
        required=True,
        label="Nom d'utilisateur ou Email",
        help_text="Entrez votre nom d'utilisateur ou votre adresse email"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        label="Mot de passe",
        help_text="Entrez votre mot de passe",
        style={'input_type': 'password'}
    )

    def validate_username(self, value):
        """Validation du champ username"""
        if not value:
            raise serializers.ValidationError("Le nom d'utilisateur est requis.")
        return value

    def validate_password(self, value):
        """Validation du champ password"""
        if not value:
            raise serializers.ValidationError("Le mot de passe est requis.")
        return value