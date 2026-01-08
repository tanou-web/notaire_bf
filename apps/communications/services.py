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

class SMSService:
    """Service d'envoi de SMS utilisant l'API Aqilas (universel Burkina Faso)"""

    @staticmethod
    def send_verification_sms(phone_number, token, user_name=None):
        """
        Envoie un SMS de vérification
        Utilise l'API Aqilas qui fonctionne avec tous les opérateurs BF

        Args:
            phone_number (str): Numéro de téléphone (format international sans +)
            token (str): Code de vérification
            user_name (str, optional): Nom de l'utilisateur

        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        from .models import CommunicationsSmslog

        # Nettoyer le numéro de téléphone
        phone_number = SMSService._normalize_phone_number(phone_number)

        # Créer le message
        greeting = f"Bonjour {user_name}, " if user_name else "Bonjour, "
        message = f"{greeting}votre code de vérification est: {token}. Valide 15 minutes. Ordre des Notaires BF"

        # Créer le log SMS en base
        sms_log = CommunicationsSmslog.objects.create(
            destinataire=phone_number,
            message=message,
            fournisseur=settings.SMS_PROVIDER,
            sender_id=getattr(settings, 'AQILAS_SENDER_ID', 'NOTAIRES'),
            statut='en_attente'
        )

        try:
            # Envoyer via le fournisseur configuré
            if settings.SMS_PROVIDER.lower() == 'aqilas':
                success, message_id, error = SMSService._send_via_aqilas(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'orange':
                success, message_id, error = SMSService._send_via_orange(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'moov':
                success, message_id, error = SMSService._send_via_moov(phone_number, message)
            else:
                # Fallback: logging pour développement
                logger.info(f"SMS simulé à {phone_number}: {message}")
                success, message_id, error = True, f"dev-{sms_log.id}", None

            # Mettre à jour le log
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
            error_msg = f"Erreur inattendue: {str(e)}"
            sms_log.statut = 'echec'
            sms_log.erreur = error_msg
            sms_log.save()
            logger.error(f"Erreur lors de l'envoi SMS à {phone_number}: {e}")
            return False, None, error_msg

    @staticmethod
    def send_payment_confirmation_sms(phone_number, transaction_reference, amount, user_name=None):
        """
        Envoie un SMS de confirmation de paiement réussi

        Args:
            phone_number (str): Numéro de téléphone du destinataire
            transaction_reference (str): Référence de la transaction
            amount (str/Decimal): Montant payé
            user_name (str, optional): Nom de l'utilisateur

        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        from .models import CommunicationsSmslog

        # Nettoyer le numéro de téléphone
        phone_number = SMSService._normalize_phone_number(phone_number)

        # Créer le message
        greeting = f"Cher(e) {user_name}," if user_name else "Cher client,"
        message = f"{greeting} votre paiement de {amount} FCFA (Ref: {transaction_reference}) a été confirmé. Merci pour votre confiance. Ordre des Notaires BF"

        # Créer le log SMS en base
        sms_log = CommunicationsSmslog.objects.create(
            destinataire=phone_number,
            message=message,
            fournisseur=settings.SMS_PROVIDER,
            sender_id=getattr(settings, 'AQILAS_SENDER_ID', 'NOTAIRES'),
            statut='en_attente',
            public_reference=f"payment-{transaction_reference}"
        )

        try:
            # Envoyer via le fournisseur configuré
            if settings.SMS_PROVIDER.lower() == 'aqilas':
                success, message_id, error = SMSService._send_via_aqilas(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'orange':
                success, message_id, error = SMSService._send_via_orange(phone_number, message)
            elif settings.SMS_PROVIDER.lower() == 'moov':
                success, message_id, error = SMSService._send_via_moov(phone_number, message)
            else:
                # Fallback: logging pour développement
                logger.info(f"SMS de paiement simulé à {phone_number}: {message}")
                success, message_id, error = True, f"dev-payment-{sms_log.id}", None

            # Mettre à jour le log
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
            error_msg = f"Erreur inattendue: {str(e)}"
            sms_log.statut = 'echec'
            sms_log.erreur = error_msg
            sms_log.save()
            logger.error(f"Erreur lors de l'envoi SMS de paiement à {phone_number}: {e}")
            return False, None, error_msg

    @staticmethod
    def _send_via_aqilas(phone_number, message):
        """
        Envoi via l'API Aqilas (SMS universel Burkina Faso)

        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        try:
            url = f"{settings.AQILAS_API_URL}/sms/send"
            headers = {
                'Authorization': f"Bearer {settings.AQILAS_API_KEY}",
                'Content-Type': 'application/json'
            }

            payload = {
                'to': phone_number,
                'message': message,
                'from': getattr(settings, 'AQILAS_SENDER_ID', 'NOTAIRES'),
                'type': 'transactional'
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=settings.AQILAS_TIMEOUT
            )

            response_data = response.json()

            if response.status_code == 200 and response_data.get('success'):
                message_id = response_data.get('message_id') or response_data.get('id')
                cost = response_data.get('cost')
                return True, message_id, None
            else:
                error_msg = response_data.get('message', f'Erreur HTTP {response.status_code}')
                return False, None, error_msg

        except requests.exceptions.Timeout:
            return False, None, "Timeout de l'API Aqilas"
        except requests.exceptions.RequestException as e:
            return False, None, f"Erreur de connexion: {str(e)}"
        except Exception as e:
            return False, None, f"Erreur API Aqilas: {str(e)}"

    @staticmethod
    def _send_via_orange(phone_number, message):
        """
        Envoi via l'API Orange SMS (maintenu pour compatibilité)

        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
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
                return True, f"orange-{int(datetime.now().timestamp())}", None
            else:
                return False, None, f"Erreur API Orange: {response.status_code}"

        except Exception as e:
            return False, None, f"Erreur Orange: {str(e)}"

    @staticmethod
    def _send_via_moov(phone_number, message):
        """
        Envoi via l'API Moov Africa (maintenu pour compatibilité)

        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
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
            else:
                return False, None, f"Erreur API Moov: {response.status_code}"

        except Exception as e:
            return False, None, f"Erreur Moov: {str(e)}"

    @staticmethod
    def _normalize_phone_number(phone_number):
        """
        Normalise le numéro de téléphone au format international

        Args:
            phone_number (str): Numéro de téléphone

        Returns:
            str: Numéro normalisé sans le +
        """
        # Supprimer les espaces et caractères spéciaux
        phone_number = ''.join(filter(str.isdigit, phone_number))

        # Ajouter le préfixe 226 si nécessaire
        if phone_number.startswith('0'):
            phone_number = '226' + phone_number[1:]
        elif not phone_number.startswith('226'):
            phone_number = '226' + phone_number

        return phone_number