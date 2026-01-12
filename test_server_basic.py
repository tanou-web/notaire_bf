#!/usr/bin/env python
"""
Test de base du serveur - vérification que les endpoints répondent
"""
import requests
import time

def test_basic_endpoints():
    """Tester les endpoints de base"""
    base_url = "http://localhost:8000"  # À adapter selon votre configuration

    endpoints_to_test = [
        ("/api/auth/login/", "POST", {"username": "test", "password": "test"}),
        ("/api/auth/register/", "POST", {"username": "test", "email": "test@test.com", "password": "test123"}),
        ("/api/geographie/regions/", "GET", None),
        ("/api/actualites/actualites/", "GET", None),
    ]

    print("🧪 TEST DES ENDPOINTS DE BASE")
    print("=" * 40)

    for endpoint, method, data in endpoints_to_test:
        try:
            url = base_url + endpoint
            print(f"\n🔍 Test {method} {endpoint}")

            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)

            print(f"   Status: {response.status_code}")

            if response.status_code >= 500:
                print("   ❌ ERREUR 500 - Serveur crash"                try:
                    error_content = response.text[:200]
                    print(f"   Contenu: {error_content}")
                except:
                    print("   Impossible de lire le contenu")
            elif response.status_code >= 400:
                print("   ⚠️  Erreur client (normal pour les tests)"            elif response.status_code < 300:
                print("   ✅ OK"            else:
                print(f"   ⚠️  Status inattendu: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNEXION IMPOSSIBLE - Serveur non démarré ou URL incorrecte")
            print("   💡 Vérifiez que le serveur tourne sur le bon port"
        except requests.exceptions.Timeout:
            print("   ⏰ TIMEOUT - Serveur trop lent à répondre"
        except Exception as e:
            print(f"   ❌ ERREUR INATTENDUE: {str(e)}")

        time.sleep(0.5)  # Petite pause entre les tests

    print("\n" + "=" * 40)
    print("📋 INSTRUCTIONS DE DÉPANNAGE:")
    print("1. Vérifiez que le serveur Django tourne: python manage.py runserver")
    print("2. Vérifiez le port (par défaut 8000)")
    print("3. Vérifiez les logs Django pour les erreurs 500")
    print("4. Appliquez les migrations: python manage.py migrate")

if __name__ == '__main__':
    test_basic_endpoints()