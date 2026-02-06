import hmac
import hashlib
import json
import requests
from django.conf import settings
from .base import PaymentProvider

class YengapayService(PaymentProvider):
    """Service d'intégration API Yengapay"""
    
    def get_config(self):
        return {
            'api_url': getattr(settings, 'YENGAPAY_API_URL', 'https://api.yengapay.com/api/v1'),
            'api_key': getattr(settings, 'YENGAPAY_API_KEY', ''),
            'organization_id': getattr(settings, 'YENGAPAY_ORGANIZATION_ID', ''),
            'project_id': getattr(settings, 'YENGAPAY_PROJECT_ID', ''),
            'webhook_secret': getattr(settings, 'YENGAPAY_WEBHOOK_SECRET', ''),
        }
    
    def initiate_payment(self):
        """Initier un paiement avec l'API Yengapay (Paiement Indirect)"""
        missing = []
        if not self.config['organization_id']:
            missing.append('organization_id')
        if not self.config['project_id']:
            missing.append('project_id')
            
        if missing:
            return {
                'success': False,
                'error': f"Configuration manquante: {', '.join(missing)} (Vérifiez le .env)",
                'api_data': {'config_seen': {k: v for k, v in self.config.items() if k != 'webhook_secret'}}
            }

        endpoint = f"groups/{self.config['organization_id']}/payment-intent/{self.config['project_id']}"
        url = f"{self.config['api_url']}/{endpoint}"
        
        headers = {
            'x-api-key': self.config['api_key'],
            'Content-Type': 'application/json'
        }
        
        # Le montant total ne doit plus inclure la commission de 3% ajoutée manuellement
        # car Yengapay s'en charge.
        amount = max(int(self.transaction.montant), 200)
        
        payload = {
            "paymentAmount": amount,
            "reference": self.transaction.reference,
            "articles": [
                {
                    "title": f"Paiement Demande #{self.transaction.demande.id}",
                    "description": f"Demande de service notarial - Ref: {self.transaction.reference}",
                    "price": amount
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # La doc indique que l'URL est dans checkoutPageUrlWithPaymentToken
            payment_url = data.get('checkoutPageUrlWithPaymentToken')
            
            if payment_url:
                return {
                    'success': True,
                    'payment_url': payment_url,
                    'transaction_id': data.get('id'), # ID interne Yengapay
                    'api_data': data
                }
            else:
                return {
                    'success': False,
                    'error': "URL de paiement non trouvée dans la réponse API.",
                    'api_data': data
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur API Yengapay: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg = f"{error_msg} - {e.response.json()}"
                except:
                    error_msg = f"{error_msg} - {e.response.text}"
            
            return {
                'success': False,
                'error': error_msg,
                'api_data': getattr(e, 'response', {}).json() if hasattr(e, 'response') and e.response is not None else {}
            }

    def verify_payment(self, transaction_id):
        """Vérifier le statut d'un paiement Yengapay"""
        # La doc propose: GET https://api.yengapay.com/api/v1/groups/{organization_id}/payment-intent/project/{project_id}/intent/{id}
        endpoint = f"groups/{self.config['organization_id']}/payment-intent/project/{self.config['project_id']}/intent/{transaction_id}"
        url = f"{self.config['api_url']}/{endpoint}"
        
        headers = {
            'x-api-key': self.config['api_key']
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Mapping des statuts Yengapay vers le système local
            # La doc mentionne transactionStatus: "PENDING", et dans webhook paymentStatus: "DONE"
            status_mapping = {
                'DONE': 'reussi',
                'SUCCESS': 'reussi',
                'PENDING': 'en_attente',
                'FAILED': 'echec',
                'CANCELLED': 'echec'
            }
            
            # Yengapay semble utiliser transactionStatus pour les intents
            remote_status = data.get('transactionStatus') or data.get('paymentStatus')
            
            return {
                'success': True,
                'status': status_mapping.get(remote_status, 'en_attente'),
                'api_data': data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'api_data': {}
            }

    def verify_webhook_signature(self, payload, signature):
        """Vérification de la signature du webhook Yengapay (HMAC SHA256)"""
        if not self.config['webhook_secret'] or not signature:
            return False
            
        # PHP example from doc:
        # $data = json_encode($request->all(),JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
        # $payloadHashed = hash_hmac('sha256', $data, $webhookSecret);
        
        # Note: In Python, we need to ensure the JSON formatting matches exactly what Yengapay sends.
        # usually separators=(',', ':') is used for compact JSON.
        data_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        
        expected_signature = hmac.new(
            self.config['webhook_secret'].encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
