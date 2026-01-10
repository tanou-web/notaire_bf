import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    '''Pour les emails professionnels.'''
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
            if result:
                logger.info(f"Contact email envoyé de {sender_email} vers {recipients}")
                return True, 'sent'
            else:
                logger.error(f"Envoi de contact email échoué: {sender_email} -> {recipients}")
                return False, 'no-delivery'
        except Exception as e:
            logger.exception(f"Erreur lors de l'envoi du contact email: {e}")
            return False, str(e)


class SMSService:
    """Service d'envoi de SMS utilisant l'API Aqilas (universel Burkina Faso)"""

    @staticmethod
    def send_verification_sms(phone_number, token, user_name=None):
        from .models import CommunicationsSmslog

        phone_number = SMSService._normalize_phone_number(phone_number)
        greeting = f"Bonjour {user_name}, " if user_name else "Bonjour, "
        message = f"{greeting}votre code de vérification est: {token}. Valide 15 minutes. Ordre des Notaires BF"

        sms_log = CommunicationsSmslog.objects.create(
            destinataire=phone_number,
            message=message,
            fournisseur=settings.SMS_PROVIDER,
            sender_id=getattr(settings, 'AQILAS_SENDER_ID', 'ONBF'),
            statut='en_attente'
        )

        try:
            if settings.SMS_PROVIDER.lower() == 'aqilas':
                success, message_id, error = SMSService._send_via_aqilas(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'orange':
                success, message_id, error = SMSService._send_via_orange(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'moov':
                success, message_id, error = SMSService._send_via_moov(phone_number, message)
            else:
                logger.info(f"SMS simulé à {phone_number}: {message}")
                success, message_id, error = True, f"dev-{sms_log.id}", None

            sms_log.statut = 'envoye' if success else 'echec'
            sms_log.message_id = message_id
            sms_log.erreur = error
            sms_log.save()

            if success:
                logger.info(f"SMS envoyé avec succès à {phone_number} (ID: {message_id})")
            else:
                logger.error(f"Échec envoi SMS à {phone_number}: {error}")

            return success, message_id, error
        except Exception as e:
            sms_log.statut = 'echec'
            sms_log.erreur = f"Erreur inattendue: {str(e)}"
            sms_log.save()
            logger.error(f"Erreur lors de l'envoi SMS à {phone_number}: {e}")
            return False, None, str(e)

    @staticmethod
    def send_payment_confirmation_sms(phone_number, transaction_reference, amount, user_name=None):
        from .models import CommunicationsSmslog

        phone_number = SMSService._normalize_phone_number(phone_number)
        greeting = f"Cher(e) {user_name}," if user_name else "Cher client,"
        message = f"{greeting} votre paiement de {amount} FCFA (Ref: {transaction_reference}) a été confirmé. Merci pour votre confiance. Ordre des Notaires BF"

        sms_log = CommunicationsSmslog.objects.create(
            destinataire=phone_number,
            message=message,
            fournisseur=settings.SMS_PROVIDER,
            sender_id=getattr(settings, 'AQILAS_SENDER_ID', 'NOTAIRES'),
            statut='en_attente',
            public_reference=f"payment-{transaction_reference}"
        )

        try:
            if settings.SMS_PROVIDER.lower() == 'aqilas':
                success, message_id, error = SMSService._send_via_aqilas(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'orange':
                success, message_id, error = SMSService._send_via_orange(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'moov':
                success, message_id, error = SMSService._send_via_moov(phone_number, message)
            else:
                logger.info(f"SMS de paiement simulé à {phone_number}: {message}")
                success, message_id, error = True, f"dev-payment-{sms_log.id}", None

            sms_log.statut = 'envoye' if success else 'echec'
            sms_log.message_id = message_id
            sms_log.erreur = error
            sms_log.save()

            if success:
                logger.info(f"SMS de confirmation de paiement envoyé à {phone_number} (Ref: {transaction_reference})")
            else:
                logger.error(f"Échec envoi SMS de paiement à {phone_number}: {error}")

            return success, message_id, error
        except Exception as e:
            sms_log.statut = 'echec'
            sms_log.erreur = f"Erreur inattendue: {str(e)}"
            sms_log.save()
            logger.error(f"Erreur lors de l'envoi SMS de paiement à {phone_number}: {e}")
            return False, None, str(e)

    @staticmethod
    def _send_via_aqilas(phone_number, message):
        """
        Envoi via l'API Aqilas (Burkina Faso)
        Requiert :
            - settings.AQILAS_TOKEN
            - settings.AQILAS_SENDER = "ONBF"
        Returns:
            (success: bool, message_id: str | None, error: str | None)
        """
        try:
            if not getattr(settings, 'AQILAS_TOKEN', None):
                return False, None, "AQILAS_TOKEN manquant dans settings"

            url = "https://www.aqilas.com/api/v1/sms"

            headers = {
                "X-AUTH-TOKEN": settings.AQILAS_TOKEN,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            payload = {
                "from": settings.AQILAS_SENDER,   # ONBF
                "text": message,
                "to": [f"+{phone_number}"],       # +226XXXXXXXX
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=getattr(settings, "AQILAS_TIMEOUT", 30),
            )

            logger.info(f"AQILAS STATUS: {response.status_code}")
            logger.info(f"AQILAS BODY: {response.text}")

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    # Cas très rare : 200 mais non JSON
                    return True, f"aqilas-{phone_number}-{int(datetime.now().timestamp())}", None

                if data.get("success") is True:
                    # Aqilas retourne bulk_id
                    return True, data.get("bulk_id"), None

                return False, None, data.get("message", "Erreur Aqilas inconnue")

            if response.status_code == 401:
                return False, None, "HTTP 401: Token Aqilas invalide"

            if response.status_code == 404:
                return False, None, "HTTP 404: Endpoint Aqilas introuvable"

            return False, None, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            return False, None, f"Connexion Aqilas impossible: {str(e)}"


    @staticmethod
    def _send_via_orange(phone_number, message):
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
                        'outboundSMSTextMessage': {'message': message}
                    }
                },
                timeout=10
            )

            if response.status_code == 201:
                return True, f"orange-{int(datetime.now().timestamp())}", None
            return False, None, f"Erreur API Orange: {response.status_code}"
        except Exception as e:
            return False, None, f"Erreur Orange: {str(e)}"

    @staticmethod
    def _send_via_moov(phone_number, message):
        try:
            response = requests.post(
                'https://api.moov.africa/sms/v1/messages',
                auth=(settings.MOOV_API_KEY, settings.MOOV_API_SECRET),
                json={
                    'to': phone_number,
                    'from': getattr(settings, 'AQILAS_SENDER_ID', 'NOTAIRES'),
                    'message': message,
                    'type': 'transactional'
                },
                timeout=10
            )

            if response.status_code == 200:
                return True, f"moov-{int(datetime.now().timestamp())}", None
            return False, None, f"Erreur API Moov: {response.status_code}"
        except Exception as e:
            return False, None, f"Erreur Moov: {str(e)}"

    @staticmethod
    def _normalize_phone_number(phone_number):
        """
        Normalise le numéro au format international (226xxxxxxxx)
        """
        phone_number = ''.join(filter(str.isdigit, phone_number))
        if phone_number.startswith('0'):
            phone_number = '226' + phone_number[1:]
        elif not phone_number.startswith('226'):
            phone_number = '226' + phone_number
        return phone_number

