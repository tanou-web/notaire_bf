from .yengapay import YengapayService


def get_payment_service(transaction):
    """Factory pour obtenir le service de paiement approprié"""
    provider_map = {
        'yengapay': YengapayService,
        'orange_money': YengapayService,  # Rétro-compatibilité: redirect Orange to Yengapay
        'moov_money': YengapayService,    # Rétro-compatibilité: redirect Moov to Yengapay
    }
    
    provider_class = provider_map.get(transaction.type_paiement)
    if not provider_class:
        raise ValueError(f"Provider de paiement non supporté: {transaction.type_paiement}")
    
    return provider_class(transaction)