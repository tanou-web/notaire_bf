import os
import requests
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_yengapay_connection():
    # Récupérer les identifiants
    api_url = os.getenv('YENGAPAY_API_URL', 'https://api.yengapay.com/api/v1')
    api_key = os.getenv('YENGAPAY_API_KEY')
    org_id = os.getenv('YENGAPAY_ORGANIZATION_ID')
    project_id = os.getenv('YENGAPAY_PROJECT_ID')

    print("=== TEST CONNECTION YENGAPAY ===")
    print(f"URL: {api_url}")
    print(f"Organization ID: {org_id}")
    print(f"Project ID: {project_id}")
    print(f"API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")
    print("-" * 30)

    if not all([api_key, org_id, project_id]):
        print("ERREUR: Variables manquantes dans le .env")
        return

    # Endpoint exact qui échoue
    endpoint = f"groups/{org_id}/payment-intent/{project_id}"
    url = f"{api_url}/{endpoint}"

    print(f"Test POST vers: {url}")

    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }

    # Payload minimal
    payload = {
        "paymentAmount": 200,
        "reference": "TEST-DEBUG-001",
        "articles": [
            {
                "title": "Test Debug",
                "description": "Test de connexion",
                "price": 200
            }
        ]
    }

    try:
        print("\nEnvoi de la requête...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response Body:", json.dumps(response.json(), indent=2))
        except:
            print("Response Text:", response.text)

        if response.status_code == 403:
            print("\n ANALYSE 403 FORBIDDEN:")
            print("1. La API Key est invalide OU")
            print("2. La API Key ne correspond pas à l'Organization ID indiqué OU")
            print("3. La API Key n'a pas les droits 'Payment' sur ce projet.")
        elif response.status_code == 200:
            print("\n SUCCÈS ! Les identifiants sont corrects.")
            
    except Exception as e:
        print(f"\nErreur technique lors de la requête: {e}")

if __name__ == "__main__":
    test_yengapay_connection()
