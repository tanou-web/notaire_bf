import requests
import sys
from datetime import datetime

# -------------------------
# CONFIGURATION
# -------------------------
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123"

HEADERS = {}
REPORT = []

# Endpoints à tester
ENDPOINTS = {
    "notaires": "/api/notaires/",
    "documents": "/api/documents/",
    "demandes": "/api/demandes/",
    "paiements": "/api/paiements/",
    "actualites": "/api/actualites/",
    "partenaires": "/api/partenaires/",
    "conseils": "/api/conseils/",
    "organisation": "/api/organisation/",
    "contact-info": "/api/contact/info/",
    "contact-form": "/api/contact/form/",
    "ventes": "/api/ventes/",
    "stats": "/api/stats/",
    "communications": "/api/communications/",
    "audit": "/api/audit/logs/",
    "system": "/api/system/",
    "core": "/api/core/",
}

# -------------------------
# UTILS
# -------------------------
def log_result(name, status, info=""):
    REPORT.append((name, status, info))
    symbol = "✅" if status == "OK" else "❌"
    print(f"{symbol} {name}: {info}")

# -------------------------
# 1. AUTHENTIFICATION
# -------------------------
def get_jwt_token():
    url = f"{BASE_URL}/api/token/"
    data = {"username": USERNAME, "password": PASSWORD}
    try:
        r = requests.post(url, json=data, timeout=10)
        if r.status_code == 200:
            token = r.json().get("access")
            log_result("JWT Token obtenu", "OK")
            return token
        else:
            log_result("JWT Token obtenu", "FAIL", f"{r.status_code} - {r.text}")
            return None
    except requests.exceptions.RequestException as e:
        log_result("JWT Token obtenu", "FAIL", str(e))
        return None

# -------------------------
# 2. TEST DES ENDPOINTS CRUD
# -------------------------
def test_endpoints(headers):
    for name, path in ENDPOINTS.items():
        url = f"{BASE_URL}{path}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            status = "OK" if r.status_code == 200 else "FAIL"
            log_result(name, status, f"HTTP {r.status_code}")
        except requests.exceptions.RequestException as e:
            log_result(name, "FAIL", str(e))

# -------------------------
# 3. TEST SMS AQILAS
# -------------------------
def test_sms():
    try:
        from apps.communications.services import SMSService
        success, message_id, error = SMSService.send_verification_sms("+22666342505", "123456", "Test Script")
        if success:
            log_result("SMS Aqilas", "OK", f"ID: {message_id}")
        else:
            log_result("SMS Aqilas", "FAIL", error)
    except ModuleNotFoundError:
        log_result("SMS Aqilas", "FAIL", "Module 'apps.communications' introuvable")
    except Exception as e:
        log_result("SMS Aqilas", "FAIL", str(e))

# -------------------------
# 4. TEST RECHERCHES ET FILTRAGES
# -------------------------
def test_search(headers):
    test_paths = [
        "/api/actualites/?q=test",
        "/api/conseils/?q=test",
        "/api/demandes/?q=test&page=1",
        "/api/audit/logs/?module=notaires",
    ]
    for path in test_paths:
        url = f"{BASE_URL}{path}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            status = "OK" if r.status_code == 200 else "FAIL"
            log_result(f"Recherche {path}", status, f"HTTP {r.status_code}")
        except requests.exceptions.RequestException as e:
            log_result(f"Recherche {path}", "FAIL", str(e))

# -------------------------
# 5. TEST DASHBOARDS
# -------------------------
def test_dashboards(headers):
    dashboard_paths = [
        "/api/ventes/statistiques/notaires/",
        "/api/stats/dashboard/",
    ]
    for path in dashboard_paths:
        url = f"{BASE_URL}{path}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            status = "OK" if r.status_code == 200 else "FAIL"
            log_result(f"Dashboard {path}", status, f"HTTP {r.status_code}")
        except requests.exceptions.RequestException as e:
            log_result(f"Dashboard {path}", "FAIL", str(e))

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    print(f"=== TEST BACKEND COMPLET ({datetime.now()}) ===")
    token = get_jwt_token()
    if not token:
        print("Impossible de récupérer le JWT. Abandon des tests.")
        sys.exit(1)

    HEADERS = {"Authorization": f"Bearer {token}"}

    # Test endpoints CRUD
    test_endpoints(HEADERS)

    # Test SMS
    test_sms()

    # Test recherches
    test_search(HEADERS)

    # Test dashboards
    test_dashboards(HEADERS)

    print("=== FIN TEST ===")
