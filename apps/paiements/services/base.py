from abc import ABC, abstractmethod
import requests
import json
import hashlib
import hmac
from django.conf import settings
from django.utils import timezone
from rest_framework import status


class PaymentProvider(ABC):
    """Classe de base pour tous les fournisseurs de paiement"""
    
    def __init__(self, transaction):
        self.transaction = transaction
        self.config = self.get_config()
    
    @abstractmethod
    def get_config(self):
        """Récupérer la configuration du provider"""
        pass
    
    @abstractmethod
    def initiate_payment(self):
        """Initier un paiement avec l'API du provider"""
        pass
    
    @abstractmethod
    def verify_payment(self, transaction_id):
        """Vérifier le statut d'un paiement"""
        pass
    
    @abstractmethod
    def verify_webhook_signature(self, payload, signature):
        """Vérifier la signature du webhook"""
        pass
    
    def create_signature(self, data):
        """Créer une signature pour les requêtes"""
        message = json.dumps(data, separators=(',', ':'))
        return hmac.new(
            self.config['api_secret'].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def make_request(self, method, endpoint, data=None):
        """Faire une requête HTTP à l'API du provider"""
        url = f"{self.config['api_url']}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.config['api_key']}",
            'X-Signature': self.create_signature(data) if data else '',
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur API {self.__class__.__name__}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', 500)
            }