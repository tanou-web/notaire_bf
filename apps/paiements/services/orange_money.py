import hmac
from .base import PaymentProvider
from django.conf import settings

class OrangeMoneyService(PaymentProvider):
    'Service d integration API Orange'
    def get_config(self):
        return{
            'api_url': settings.ORANGE_MONEY_API_URL,
            'api_key': settings.ORANGE_MONEY_API_KEY,
            'api_secret': settings.ORANGE_MONEY_API_SECRET,
            'merchant_code': settings.ORANGE_MONEY_MERCHANT_CODE,
            'callback_url': settings.ORANGE_MONEY_CALLBACK_URL,
        }
    
    def initiate_payment(self):
        'initier un payement'
        #donnee a envoyer a api
        payment_data ={
            'merchant_code':self.config['merchant_code'],
            'amount':str(float(self.transaction.montant)),
            'currency':'XOF',
            'order_id': self.transaction.reference,
            'return_url': f'{self.config['callback_url']}?transaction_id={self.transaction.reference}',
            'cancel_url': f'{self.config['callback_url']}?transaction_id={self.transaction.reference}&status=cancelled',
            'notif_url':f'{settings.BASE_URL}/api/paiements/webhook/orange_money',
            'lang': 'fr',
            'reference': self.transaction.reference
        }
        #appel de l api OrangeMoney
        response = self.make_request('POST', 'api/payment/v1/init', payment_data)

        if response.get('success', False):
            return {
                'success': True,
                'payment_url': response['data']['payment_url'],
                'transaction_id': response['data']['transaction_id'],
                'api_data':response
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Erreur inconnue'),
                'api_data':response
            }
        def verify_payment(self, transaction_id):
            'verifier le status d un payement'
            verify_data = {
                'merchant_code':self.config['merchant_code'],
                'transaction_id': transaction_id,
            }
            response =self.make_requests('POST', 'api/payment/v1/verify', verify_data)
            if response.get('success',False):
                status_mapping ={
                    'SUCCESS':'reussi',
                    'PENDING': 'en_attente',
                    'FAILED':'echec',
                    'CANCELLED':'echec'
                }
                return {
                    'success': True,
                    'status':status_mapping.get(response['data']['status'], 'en_attente'),
                    'api_data':response
                }
            else:
                return{
                    'success': False,
                    'error':response.get('error','Erreur de verification'),
                    'api_data':response
                }
    def verify_webhook_signature(self, payload, signature):
        'verification de la signature du webhook Orange Money'
        expected_signature = self.create_signature(payload)
        return hmac.compare_digest(expected_signature, signature)