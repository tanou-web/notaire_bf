import requests
from django.conf import settings

def send_otp_sms(phone, otp):
    """
    Envoi d'OTP via l'API Aqilas
    Utilise l'API_KEY/API_SECRET si disponible, sinon AQILAS_TOKEN
    """
    try:
        # Essayer d'abord avec API_KEY/API_SECRET (méthode recommandée)
        if hasattr(settings, 'AQILAS_API_KEY') and settings.AQILAS_API_KEY:
            return _send_via_api_key(phone, otp)
        # Sinon utiliser le token direct
        elif hasattr(settings, 'AQILAS_TOKEN') and settings.AQILAS_TOKEN:
            return _send_via_token(phone, otp)
        else:
            print("Erreur: Aucune configuration SMS trouvée (ni API_KEY ni TOKEN)")
            return 0

    except Exception as e:
        print(f"Erreur générale SMS: {e}")
        return 0


def _send_via_api_key(phone, otp):
    """Envoi via API_KEY/API_SECRET (méthode standard Aqilas)"""
    try:
        # URL basée sur les tests effectués
        url = "https://www.aqilas.com/api/v1/sms/send"

        # Formater le numéro avec +226
        if not phone.startswith('+'):
            phone_number = f"+{phone}"
        else:
            phone_number = phone

        headers = {
            "Authorization": f"Bearer {settings.AQILAS_API_KEY}",
            "Accept": "application/json"
        }

        # L'API Aqilas attend probablement POST avec JSON body
        # Essayer POST au lieu de GET
        payload = {
            "contacts": phone_number,
            "senderid": settings.AQILAS_SENDER_ID or "NOTAIRES",
            "message": f"Votre code OTP est : {otp}"
        }

        # Ajouter Content-Type pour POST
        headers["Content-Type"] = "application/json"

        response = requests.post(url, headers=headers, json=payload, timeout=getattr(settings, 'AQILAS_TIMEOUT', 30))

        print(f"Aqilas API_KEY Status: {response.status_code}")
        print(f"Aqilas API_KEY Response: {response.text}")

        return response.status_code

    except requests.exceptions.RequestException as e:
        print(f"Erreur connexion API_KEY: {e}")
        return 0


def _send_via_token(phone, otp):
    """Envoi via TOKEN direct - selon documentation officielle Aqilas"""
    try:
        # URL exacte de la documentation
        url = "https://www.aqilas.com/api/v1/sms"

        headers = {
            "X-AUTH-TOKEN": settings.AQILAS_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Format exact selon documentation
        payload = {
            "from": settings.AQILAS_SENDER or "NOTAIRES",
            "text": f"Votre code OTP est : {otp}",
            "to": [phone]  # Doit être un array selon doc
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"Aqilas TOKEN Status: {response.status_code}")
        print(f"Aqilas TOKEN Response: {response.text}")

        # Vérifier la réponse selon documentation
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("success") == True:
                    print(f"SMS envoyé - Coût: {data.get('cost', 'N/A')} {data.get('currency', 'XOF')}")
                    return 200
                else:
                    print(f"Erreur Aqilas: {data.get('message', 'Erreur inconnue')}")
                    return 400
            except:
                return response.status_code
        else:
            return response.status_code

    except requests.exceptions.RequestException as e:
        print(f"Erreur connexion TOKEN: {e}")
        return 0