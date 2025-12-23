import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string
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
        verification_link = f"{settings.FRONTEND_URL}/verify-email/?token={token}"
        
        context = {
            'user_name': user_name or 'Utilisateur',
            'verification_link': verification_link,
            'lang': lang
        }
        
        html_content = render_to_string('emails/verification_email.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
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
        
        context = {
            'user_name': user_name or 'Utilisateur',
            'lang': lang
        }
        
        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        try:
            email.send()
            logger.info(f"Email de bienvenue envoyé à {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {user_email}: {e}")

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