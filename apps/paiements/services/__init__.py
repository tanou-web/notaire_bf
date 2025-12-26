from .orange_money import OrangeMoneyService
from .moov_money import MoovMoneyService


def get_payment_service(transaction):
    """Factory pour obtenir le service de paiement approprié"""
    provider_map = {
        'orange_money': OrangeMoneyService,
        'moov_money': MoovMoneyService,
    }
    
    provider_class = provider_map.get(transaction.type_paiement)
    if not provider_class:
        raise ValueError(f"Provider de paiement non supporté: {transaction.type_paiement}")
    
    return provider_class(transaction)