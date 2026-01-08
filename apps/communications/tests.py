import unittest
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock
from .services import SMSService
from .models import CommunicationsSmslog


class SMSServiceTestCase(TestCase):
    """Tests pour le service SMS"""

    def setUp(self):
        self.test_phone = "22670000000"
        self.test_token = "123456"

    @patch('apps.communications.services.settings')
    def test_send_verification_sms_aqilas_success(self, mock_settings):
        """Test envoi SMS de vérification via Aqilas - succès"""
        mock_settings.SMS_PROVIDER = 'aqilas'
        mock_settings.AQILAS_API_KEY = 'test_key'
        mock_settings.AQILAS_SENDER_ID = 'NOTAIRES'

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'message_id': 'test_msg_123'
            }
            mock_post.return_value = mock_response

            success, message_id, error = SMSService.send_verification_sms(
                self.test_phone, self.test_token
            )

            self.assertTrue(success)
            self.assertEqual(message_id, 'test_msg_123')
            self.assertIsNone(error)

            # Vérifier que le log a été créé
            sms_log = CommunicationsSmslog.objects.filter(destinataire=self.test_phone).last()
            self.assertIsNotNone(sms_log)
            self.assertEqual(sms_log.statut, 'envoye')
            self.assertEqual(sms_log.fournisseur, 'aqilas')

    @patch('apps.communications.services.settings')
    def test_send_payment_confirmation_sms(self, mock_settings):
        """Test envoi SMS de confirmation de paiement"""
        mock_settings.SMS_PROVIDER = 'aqilas'
        mock_settings.AQILAS_API_KEY = 'test_key'
        mock_settings.AQILAS_SENDER_ID = 'NOTAIRES'

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'message_id': 'payment_msg_456'
            }
            mock_post.return_value = mock_response

            success, message_id, error = SMSService.send_payment_confirmation_sms(
                self.test_phone, "TXN-123", "15000", "John Doe"
            )

            self.assertTrue(success)
            self.assertEqual(message_id, 'payment_msg_456')
            self.assertIsNone(error)

            # Vérifier que le log a été créé avec la bonne référence
            sms_log = CommunicationsSmslog.objects.filter(
                destinataire=self.test_phone,
                public_reference='payment-TXN-123'
            ).last()
            self.assertIsNotNone(sms_log)
            self.assertEqual(sms_log.statut, 'envoye')
            self.assertIn("15000 FCFA", sms_log.message)
            self.assertIn("TXN-123", sms_log.message)

    @patch('apps.communications.services.settings')
    def test_send_verification_sms_aqilas_failure(self, mock_settings):
        """Test envoi SMS de vérification via Aqilas - échec"""
        mock_settings.SMS_PROVIDER = 'aqilas'
        mock_settings.AQILAS_API_KEY = 'test_key'

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                'success': False,
                'message': 'Invalid API key'
            }
            mock_post.return_value = mock_response

            success, message_id, error = SMSService.send_verification_sms(
                self.test_phone, self.test_token
            )

            self.assertFalse(success)
            self.assertIsNone(message_id)
            self.assertEqual(error, 'Invalid API key')

            # Vérifier que le log a été créé avec l'erreur
            sms_log = CommunicationsSmslog.objects.filter(destinataire=self.test_phone).last()
            self.assertIsNotNone(sms_log)
            self.assertEqual(sms_log.statut, 'echec')
            self.assertEqual(sms_log.erreur, 'Invalid API key')

    def test_normalize_phone_number(self):
        """Test de normalisation des numéros de téléphone"""
        # Test avec préfixe 226
        self.assertEqual(
            SMSService._normalize_phone_number("70000000"),
            "22670000000"
        )

        # Test déjà normalisé
        self.assertEqual(
            SMSService._normalize_phone_number("22670000000"),
            "22670000000"
        )

        # Test avec espaces et caractères spéciaux
        self.assertEqual(
            SMSService._normalize_phone_number("+226 70 00 00 00"),
            "22670000000"
        )

    @patch('apps.communications.services.settings')
    def test_send_verification_sms_development_mode(self, mock_settings):
        """Test envoi SMS en mode développement (fallback)"""
        mock_settings.SMS_PROVIDER = 'development'

        success, message_id, error = SMSService.send_verification_sms(
            self.test_phone, self.test_token
        )

        self.assertTrue(success)
        self.assertIsNotNone(message_id)
        self.assertIsNone(error)

        # Vérifier que le log a été créé
        sms_log = CommunicationsSmslog.objects.filter(destinataire=self.test_phone).last()
        self.assertIsNotNone(sms_log)
        self.assertEqual(sms_log.statut, 'envoye')
        self.assertEqual(sms_log.fournisseur, 'development')
