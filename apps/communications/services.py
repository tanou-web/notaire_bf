import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    '''Pour les emails professionnels .'''
    @staticmethod
    def send_verification_email(user_email, token, user_name=None, lang='fr'):
        '''Envoyer un email de vérification'''
        subject = 'Vérification de votre compte - Ordre des Notaires BF'
        verification_link = f"{getattr(settings, 'FRONTEND_URL', '')}/verify-email/?token={token}"

        html_content = (
            f"<p>Bonjour {user_name or 'Utilisateur'},</p>"
            f"<p>Veuillez vérifier votre adresse email en cliquant sur le lien suivant :</p>"
            f"<p><a href=\"{verification_link}\">{verification_link}</a></p>"
            f"<p>Si vous n'avez pas demandé cette vérification, ignorez cet email.</p>"
        )

        text_content = (
            f"Bonjour {user_name or 'Utilisateur'},\n\n"
            f"Veuillez vérifier votre adresse email en visitant le lien : {verification_link}\n\n"
            "Si vous n'avez pas demandé cette vérification, ignorez cet email."
        )

        email = EmailMultiAlternatives(
            subject,
            text_content,
            getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            [user_email]
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send()
            logger.info(f"Email de vérification envoyé à {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {user_email}: {e}")
    @staticmethod
    def send_welcome_email(user_email, user_name=None, lang='fr'):
        '''Envoyer un email de bienvenue'''
        subject = 'Bienvenue à l\'Ordre des Notaires BF'
        html_content = (
            f"<p>Bonjour {user_name or 'Utilisateur'},</p>"
            f"<p>Bienvenue à l'Ordre des Notaires BF. Nous sommes ravis de vous compter parmi nous.</p>"
        )

        text_content = (
            f"Bonjour {user_name or 'Utilisateur'},\n\n"
            "Bienvenue à l'Ordre des Notaires BF. Nous sommes ravis de vous compter parmi nous."
        )

        email = EmailMultiAlternatives(
            subject,
            text_content,
            getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            [user_email]
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send()
            logger.info(f"Email de bienvenue envoyé à {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {user_email}: {e}")

    @staticmethod
    def send_contact_email(sender_email, subject, message, sender_name=None, phone=None):
        """Send a contact message to configured recipients.

        Returns a tuple (success: bool, message_id_or_error: str).
        """
        recipients = getattr(settings, 'CONTACT_RECIPIENTS', None) or getattr(settings, 'CONTACT_EMAILS', None)
        if not recipients:
            # Fall back to ADMINS or DEFAULT_FROM_EMAIL
            admins = getattr(settings, 'ADMINS', None)
            if admins:
                recipients = [a[1] for a in admins]
            else:
                recipients = [getattr(settings, 'DEFAULT_FROM_EMAIL', sender_email)]

        html_parts = [
            f"<p>Message de la part de: {sender_name or sender_email}</p>",
            f"<p>Email: {sender_email}</p>",
        ]
        if phone:
            html_parts.append(f"<p>Téléphone: {phone}</p>")
        html_parts.append(f"<hr/><p>{message}</p>")
        html_content = "".join(html_parts)

        text_parts = [
            f"Message de la part de: {sender_name or sender_email}\n",
            f"Email: {sender_email}\n",
        ]
        if phone:
            text_parts.append(f"Téléphone: {phone}\n")
        text_parts.append("\n---\n")
        text_parts.append(f"{message}")
        text_content = "".join(text_parts)

        email = EmailMultiAlternatives(
            subject,
            text_content,
            getattr(settings, 'DEFAULT_FROM_EMAIL', sender_email),
            recipients,
            reply_to=[sender_email]
        )
        email.attach_alternative(html_content, "text/html")

        try:
            result = email.send()
            # Django's EmailMessage.send returns number of successfully delivered messages (1 if ok)
            if result:
                logger.info(f"Contact email envoyé de {sender_email} vers {recipients}")
                return True, 'sent'
            else:
                logger.error(f"Envoi de contact email échoué: {sender_email} -> {recipients}")
                return False, 'no-delivery'
        except Exception as e:
            logger.exception(f"Erreur lors de l'envoi du contact email: {e}")
            return False, str(e)

"""
class SMSService:
    #Service d'envoi de SMS (exemple avec Twilio/Orange/Moov)
    
    @staticmethod
    def send_verification_sms(phone_number, token):
        
        Envoie un SMS de vérification
        Utilise l'API du fournisseur SMS
        
        message = f"Code de vérification: {token}. Valide 15 minutes. Ordre des Notaires BF"
        
        # Exemple avec l'API Orange SMS
        if settings.SMS_PROVIDER == 'orange':
            return SMSService._send_via_orange(phone_number, message)
        
        # Exemple avec l'API Moov Africa
        elif settings.SMS_PROVIDER == 'moov':
            return SMSService._send_via_moov(phone_number, message)
        
        # Fallback: logging pour développement
        else:
            logger.info(f"SMS à envoyer à {phone_number}: {message}")
            return True
    
    @staticmethod
    def _send_via_orange(phone_number, message):
        
        Envoi via l'API Orange SMS
       
        try:
            response = requests.post(
                'https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B2260000/requests',
                headers={
                    'Authorization': f'Bearer {settings.ORANGE_API_TOKEN}',
                    'Content-Type': 'application/json'
                },
                json={
                    'outboundSMSMessageRequest': {
                        'address': f'tel:+{phone_number}',
                        'senderAddress': 'tel:+2260000',
                        'outboundSMSTextMessage': {
                            'message': message
                        }
                    }
                },
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"SMS Orange envoyé à {phone_number}")
                return True
            else:
                logger.error(f"Erreur API Orange: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur d'envoi SMS Orange: {e}")
            return False
    
    @staticmethod
    def _send_via_moov(phone_number, message):
        Envoi via l'API Moov Africa
       
        try:
            response = requests.post(
                'https://api.moov.africa/sms/v1/messages',
                auth=(settings.MOOV_API_KEY, settings.MOOV_API_SECRET),
                json={
                    'to': phone_number,
                    'from': 'NOTAIRES',
                    'message': message,
                    'type': 'transactional'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"SMS Moov envoyé à {phone_number}")
                return True
            else:
                logger.error(f"Erreur API Moov: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur d'envoi SMS Moov: {e}")
            return False
"""