import os
import django
from django.conf import settings

# Setup Django standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.paiements.services.yengapay import YengapayService
from apps.paiements.models import PaiementsTransaction
from apps.demandes.models import DemandesDemande
from django.utils import timezone
import uuid

def test_flow():
    print("=== TEST FLUX PAIEMENT SIMPLIFIÉ ===")
    
    # 1. Mocking a Transaction (in memory or creating dummy if DB allows)
    # We need a transaction to pass to the service
    
    # Creating a dummy transaction object (not saving to DB to avoid pollution if possible, 
    # but Service expects .transaction access)
    
    class MockDemande:
        id = 99999
    
    class MockTransaction:
        reference = f"TEST-REF-{uuid.uuid4().hex[:8]}"
        montant = 200
        demande = MockDemande()
        type_paiement = 'yengapay'
    
    mock_tx = MockTransaction()
    
    print(f"Transaction simulée: Ref={mock_tx.reference}, Montant={mock_tx.montant}")
    
    service = YengapayService(mock_tx)
    
    # Check config
    config = service.get_config()
    print("Configuration chargée:")
    print(f"- API URL: {config['api_url']}")
    print(f"- Project ID: {config['project_id']}")
    print(f"- Org ID: {config['organization_id']}")
    print(f"- API Key: {config['api_key'][:5]}...")
    
    if not config['api_key'] or not config['organization_id']:
        print("ERREUR: Configuration manquante dans le .env")
        return

    # Initiate
    print("\nTentative d'initiation via YengapayService...")
    try:
        result = service.initiate_payment()
        
        print("\nRésultat:")
        print(result)
        
        if result['success']:
            print("\n✅ SUCCÈS: URL de paiement générée !")
            print(f"URL: {result['payment_url']}")
        else:
            print("\n❌ ÉCHEC:", result.get('error'))
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_flow()
