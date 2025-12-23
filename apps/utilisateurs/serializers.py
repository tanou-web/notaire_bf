from rest_framework import serializers
from django.contrib.auth import get_user_model,password_validation
from django.core.validators import validate_email,RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import re
import hashlib
import secrets
import string
from datetime import timedelta,datetime
from .models import VerificationVerificationtoken


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = User
        fields = [
            'id','username','email','password',
            'nom', 'prenom','telephone',
            'is_active','is_staff','is_superuser',
            'date_joined','last_login','updated_at'
        ]
        read_only_fields = [
            'id','date_joined', 'last_login','updated_at'
            'email_verified', 'telephone_verified'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objectscreate(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        return instance
    
    class UserCreateSerializer(serializers.ModelSerializer):
        password = serializers.CharField(write_only=True)
        password_confirm = serializers.CharField(write_only=True)

        class Meta:
            model = User
            fields = [
                'username', 'email', 'password', 'password_confirm',
                'nom', 'prenom', 'telephone'
            ]
            extra_kwargs = {
                'email': {'required': True},
            }
        def validate(self, data):
            if data['password'] != data['password_confirm']:
                raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
            return data

        def create(self, validated_data):
            password = validated_data.pop('password')
            user = User.objects.create_user(password=password, **validated_data)
            return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id','username','email',
            'nom', 'prenom','telephone',
            'date_joined'
        ]

class VerificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationToken
        fields = '__all__'
        read_only_lfields = ['created_at', 'expires_at']

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
    
class SendVerificationSerializer(serializers.Serializer):
    """
     TYPE_CHOICES = [
        ('email_verification', 'Email'),
        ('sms', 'SMS'),

    verification_type = serializers.ChoiceField(choices=TYPE_CHOICES)
    email = serializers.EmailField(required=False)
    telephone = serializers.CharField(required=False)
    """
    
    email = serializers.EmailField()

    def validate(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Email invalide.")
        return value
       
        request = self.context.get('request')
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            cache_key = f"send_verification_{ip_address}"
            last_sent = cache.get(cache_key)
            if last_sent:
                raise serializers.ValidationError("Trop de demandes. Veuillez réessayer plus tard.")
            cache.set(cache_key, True, timeout=60)  # 1 minute cooldown
        return value
    
    def create(self, validated_data):
        email = validated_data.get('email')
        token = VerificationTokenGenerator.generate_token()
        token_hash = VerificationTokenGenerator.hash_token(token)
        expires_at = timezone.now() + timedelta(hours=1)

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("Utilisateur avec cet email n'existe pas.")

        verification_token = VerificationVerificationtoken.objects.create(
            user=user,
            token_hash=token_hash,
            type_token='email',
            expires_at=expires_at
            data ={
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT',''),
                'sent_at': timezone.now()
            }
        )
        verification_token = VerificationVerificationtoken.objects.filter(
            user=user,
            type_token='email',
            used=False,
            expires_at__gt=timezone.now()
        ).delete()
        """
        # Envoyer le token (simulé ici)
        if verification_type == 'email':
            self._send_email_verification(user, token, email)
        else:
            self._send_sms_verification(user, token, telephone)
        """

        self.send_email_verification(email, token, email)
        return {
            "message": "Token de vérification envoyé avec succès.",
            "token_id": verification_token.id,
            "expires_at": verification_token.expires_at
            
        }
    
    def send_email_verification(self, user, token, email):
        from django.core.mail import send_mail
        # Implémenter la logique d'envoi d'email ici
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
        
    """
     def _send_sms_verification(self, user, token, telephone):
        pour envoyer un SMS
        print(f"Envoyer SMS à {telephone} avec le token {token}")
        #Exemple avec l api sms
        import requests
        response = requests.post("https://api.smsprovider.com/send", data={
            "to": telephone,
            "message": f"Votre code de vérification est : {token}"
        })
        if response.status_code != 200:
            raise Exception("Échec de l'envoi du SMS")
    """
class VerifyTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    email = serializers.EmailField()

    def validate(self, data):
        email = data.get('email')
        token = data.get('token')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur avec cet email n'existe pas.")

        try:
            verification_token = VerificationVerificationtoken.objects.get(
                user=user,
                type_token='email',
                used=False,
                expires_at__gt=timezone.now()
            )
        except VerificationVerificationtoken.DoesNotExist:
            raise serializers.ValidationError("Token invalide ou expiré.")

        if not VerificationTokenGenerator.verify_token(verification_token.token_hash, token):
            raise serializers.ValidationError("Token invalide.")

        data['user'] = user
        data['verification_token'] = verification_token
        return data

    def save(self):
        user = self.validated_data['user']
        verification_token = self.validated_data['verification_token']

        user.email_verified = True
        user.save()

        verification_token.used = True
        verification_token.save()

        return user
    def create(self, validated_data):
        user = validated_data['user']
        verification_token = validated_data['verification_token']
        verification_type = validated_data.get('verification_type')
        verification_token.used = True
        verification_token.save()
        user.email_verified = True
        user.save()

        VerificationVerificationtoken.objects.filter(
            user=user,
            type_token=verification_type,
            used=False,
            expires_at__gt=timezone.now()
        ).delete()
        return {
            'success': True,
            'message': f'{verification_type.replace("_", " ").capitalize()} vérifié avec succès',
            'user_id': user.id
        }

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'nom', 'prenom', 'telephone',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'updated_at'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'updated_at',
            'email_verified', 'telephone_verified'
        ]
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Email invalide.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        if password:
            user.set_password(password)
            user.save()
        user.is_active = False  # Désactiver jusqu'à vérification
        user.save()
        # Envoyer l'email de vérification
        send_serializer = SendVerificationSerializer(
            data={
                'verification_type': 'email',
                'email': user.email
            },
            context=self.context
        )
        if send_serializer.is_valid():
            send_serializer.save()

        return user
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            old_password = validated_data.pop('old_password', None)
            if not instance.check_password(old_password):
                raise serializers.ValidationError({"old_password": "L'ancien mot de passe est incorrect."})
            if instance.check_password(password):
                raise serializers.ValidationError({"password": "Le nouveau mot de passe doit être différent de l'ancien."}) 
            instance.set_password(password)
            instance.last_password_change = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'nom', 'prenom', 'telephone'
        ]
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_accept_terms(self, value):
        if not value:
            raise serializers.ValidationError("Vous devez accepter les termes et conditions.")
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
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        user = User.objects.create_user(password=password, **validated_data)
        user.is_active = False  # Désactiver jusqu'à vérification
        user.save()
        # Envoyer l'email de vérification
        send_serializer = SendVerificationSerializer(
            data={
                'verification_type': 'email',
                'email': user.email
            },
            context=self.context
        )
        if send_serializer.is_valid():
            send_serializer.save()

        return user
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'nom', 'prenom', 'telephone',
            'date_joined'
        ]
class VerificationTokenSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)
    class Meta:
        model = VerificationVerificationtoken
        fields = '__all__'
        read_only_fields = ['created_at', 'expires_at']
    
class ResendVerificationSerializer(serializers.Serializer):
    """Sérialiseur pour renvoyer un token de vérification"""
    
    verification_type = serializers.ChoiceField(
        choices=[('email', 'Email'), ('sms', 'SMS')]
    )
    identifier = serializers.CharField(required=True)  # email ou téléphone
    
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
                # Ne pas révéler l'existence
                pass
        else:
            try:
                user = User.objects.get(telephone=identifier)
            except User.DoesNotExist:
                # Ne pas révéler l'existence
                pass
        
        if not user:
            # Incrementer quand même pour éviter l'énumération
            cache.set(cache_key, attempts + 1, 3600)  # 1 heure
            return data
        
        # Vérifier si un token valide existe déjà
        existing_tokens = VerificationVerificationtoken.objects.filter(
            user=user,
            type_token=verification_type,
            used=False,
            expires_at__gt=timezone.now()
        )
        
        if existing_tokens.exists():
            # Si un token valide existe déjà, on peut soit:
            # 1. Réutiliser le même token
            # 2. Invalider l'ancien et en créer un nouveau
            # Ici, on choisit d'invalider l'ancien
            existing_tokens.update(used=True)
        
        data['user'] = user
        cache.set(cache_key, attempts + 1, 3600)
        
        return data
    
    def create(self, validated_data):
        user = validated_data.get('user')
        verification_type = validated_data['verification_type']
        identifier = validated_data['identifier']
        
        if not user:
            # Pour éviter l'énumération, on retourne un succès même si l'utilisateur n'existe pas
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
            data={
                'is_resend': True,
                'original_request': timezone.now().isoformat()
            }
        )
        
        # Envoyer le token
        if verification_type == 'email':
            from apps.communications.services import EmailService
            EmailService.send_verification_email(
                user_email=identifier,
                token=token,
                user_name=f"{user.nom} {user.prenom}"
            )
        else:
            from apps.communications.services import SMSService
            SMSService.send_verification_sms(
                phone_number=identifier,
                token=token
            )
        
        # Journaliser l'action
        AuditLogger.log_token_usage(
            user=user,
            token_type='verification',
            action='resend',
            token_id=verification_token.id,
            ip_address=self.context.get('request').META.get('REMOTE_ADDR') if self.context.get('request') else None
        )
        
        return {
            "message": "Un nouveau code de vérification a été envoyé",
            "token_id": verification_token.id,
            "expires_at": verification_token.expires_at,
            "verification_type": verification_type
        }