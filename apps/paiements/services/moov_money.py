from .base import PaymentProvider
from django.conf import settings


class MoovMoneyService(PaymentProvider):
    """Service d'intégration Moov Money Burkina Faso"""
    
    def get_config(self):
        return {
            'api_url': settings.MOOV_MONEY_API_URL,
            'api_key': settings.MOOV_MONEY_API_KEY,
            'api_secret': settings.MOOV_MONEY_API_SECRET,
            'merchant_id': settings.MOOV_MONEY_MERCHANT_ID,
            'callback_url': settings.MOOV_MONEY_CALLBACK_URL,
        }
    
    def initiate_payment(self):
        """Initier un paiement Moov Money"""
        payment_data = {
            "merchantId": self.config['merchant_id'],
            "amount": str(float(self.transaction.montant)),
            "currency": "XOF",
            "orderId": self.transaction.reference,
            "description": f"Paiement document notarial {self.transaction.reference}",
            "returnUrl": f"{self.config['callback_url']}?transaction_id={self.transaction.reference}",
            "cancelUrl": f"{self.config['callback_url']}?transaction_id={self.transaction.reference}&status=cancelled",
            "notifyUrl": f"{settings.BASE_URL}/api/paiements/webhook/moov_money/",
            "customerEmail": self.transaction.demande.utilisateur.email,
            "customerPhone": self.transaction.demande.utilisateur.telephone,
        }
        
        response = self.make_request('POST', 'v2/payment/request', payment_data)
        
        if response.get('status') == 'SUCCESS':
            return {
                'success': True,
                'payment_url': response['data']['paymentUrl'],
                'transaction_id': response['data']['transactionId'],
                'api_data': response
            }
        else:
            return {
                'success': False,
                'error': response.get('message', 'Erreur inconnue'),
                'api_data': response
            }
    
    def verify_payment(self, transaction_id):
        """Vérifier le statut d'un paiement Moov Money"""
        verify_data = {
            "merchantId": self.config['merchant_id'],
            "transactionId": transaction_id,
        }
        
        response = self.make_request('POST', 'v2/payment/status', verify_data)
        
        if response.get('status') == 'SUCCESS':
            status_mapping = {
                'COMPLETED': 'reussi',
                'PENDING': 'en_attente',
                'FAILED': 'echec',
                'CANCELLED': 'echec'
            }
            
            return {
                'success': True,
                'status': status_mapping.get(response['data']['paymentStatus'], 'en_attente'),
                'api_data': response
            }
        else:
            return {
                'success': False,
                'error': response.get('message', 'Erreur de vérification'),
                'api_data': response
            }
    
    def verify_webhook_signature(self, payload, signature):
        """Vérifier la signature du webhook Moov Money"""
        # Moov Money utilise généralement un header X-Signature différent
        message = f"{payload['transactionId']}{payload['amount']}{payload['status']}"
        expected_signature = hmac.new(
            self.config['api_secret'].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)