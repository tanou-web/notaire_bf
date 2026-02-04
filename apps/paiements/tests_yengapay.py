import json
import hmac
import hashlib
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock
from apps.paiements.models import PaiementsTransaction
from apps.demandes.models import DemandesDemande
from apps.utilisateurs.models import User
from apps.paiements.services.yengapay import YengapayService

class YengapayIntegrationTest(TestCase):
    def setUp(self):
        # 1. Créer l'utilisateur requis par Demande
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            nom='Test',
            prenom='User',
            telephone='22675757575'
        )

        # 2. Créer le document requis par Demande
        from apps.documents.models import DocumentsDocument
        self.doc = DocumentsDocument.objects.create(
            reference='DOC-TEST-001',
            nom='Test Document',
            description='Test Description',
            prix=5000,
            delai_heures=120
        )

        # 3. Créer la demande
        self.demande = DemandesDemande.objects.create(
            utilisateur=self.user,
            statut='attente_paiement',
            montant_total=5000,
            reference='DEM-12345',
            document=self.doc
        )

        # 4. Créer la transaction (commission à 0)
        self.transaction = PaiementsTransaction.objects.create(
            demande=self.demande,
            type_paiement='yengapay',
            montant=5000,
            commission=0,
            reference='TX-YENGAPAY-TEST',
            statut='initiee' # Statut correct dans le modèle
        )
        self.service = YengapayService(self.transaction)

    @patch('requests.post')
    def test_initiate_payment_success(self, mock_post):
        # Mock successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'checkoutPageUrlWithPaymentToken': 'https://api.yengapay.com/checkout/token123',
            'id': 'yenga-id-123'
        }
        
        # We need to set organization_id for the test
        with patch.object(settings, 'YENGAPAY_ORGANIZATION_ID', 'test-org'):
            self.service.config['organization_id'] = 'test-org'
            result = self.service.initiate_payment()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_url'], 'https://api.yengapay.com/checkout/token123')
        self.assertEqual(result['transaction_id'], 'yenga-id-123')

    def test_verify_webhook_signature(self):
        payload = {'reference': 'TX-YENGAPAY-TEST', 'paymentStatus': 'DONE'}
        webhook_secret = 'test-secret'
        
        data_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        self.service.config['webhook_secret'] = webhook_secret
        
        self.assertTrue(self.service.verify_webhook_signature(payload, signature))
        self.assertFalse(self.service.verify_webhook_signature(payload, 'wrong-signature'))

    @patch('apps.paiements.services.get_payment_service')
    def test_webhook_view_success(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.verify_webhook_signature.return_value = True
        mock_get_service.return_value = mock_service
        
        url = reverse('paiements:webhook-yengapay')
        payload = {
            'reference': 'TX-YENGAPAY-TEST',
            'paymentStatus': 'DONE'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_WEBHOOK_HASH='valid-signature' # In real case, signature would be validated by mock
        )
        
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.statut, 'validee')
        self.demande.refresh_from_db()
        self.assertEqual(self.demande.statut, 'en_attente_traitement')
