import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from django.conf import settings

print('=== DIAGNOSTIC CONFIGURATION SMS ===')
api_key = getattr(settings, 'AQILAS_API_KEY', 'NON DEFINI')
token = getattr(settings, 'AQILAS_TOKEN', 'NON DEFINI')

print(f'AQILAS_API_KEY: {api_key}')
print(f'AQILAS_TOKEN: {token}')

# Vérifier quelle méthode sera utilisée
if hasattr(settings, 'AQILAS_API_KEY') and settings.AQILAS_API_KEY and settings.AQILAS_API_KEY != 'votre-cle-api-aqilas':
    print('Methode utilisee: API_KEY/API_SECRET')
    method = 'api_key'
elif hasattr(settings, 'AQILAS_TOKEN') and settings.AQILAS_TOKEN:
    print('Methode utilisee: TOKEN direct')
    method = 'token'
else:
    print('Aucune methode disponible - SMS ne fonctionnera pas')
    method = 'none'

print(f'AQILAS_SENDER_ID: {getattr(settings, "AQILAS_SENDER_ID", "NON DEFINI")}')
print(f'AQILAS_SENDER: {getattr(settings, "AQILAS_SENDER", "NON DEFINI")}')

print('\n=== DETAILS DE LA METHODE ACTUELLE ===')
if method == 'api_key':
    print('URL: https://www.aqilas.com/api/v1/sms/send')
    print('Methode HTTP: GET')
    print('Headers: Authorization: Bearer {API_KEY}')
    print('Parametres: to, message, from')
elif method == 'token':
    print('URL: https://www.aqilas.com/api/v1/sms')
    print('Methode HTTP: POST')
    print('Headers: X-AUTH-TOKEN: {TOKEN}')
    print('Payload: contacts, senderid, msg')
else:
    print('Aucune methode configuree')

print('\n=== TEST API AQUILAS ===')
import requests

if method == 'api_key':
    # Test méthode API_KEY
    url = 'https://www.aqilas.com/api/v1/sms/send'
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'to': '+22670000000', 'message': 'Test OTP: 123456', 'from': 'NOTAIRES'}

    print(f'Test URL: {url}')
    print(f'Headers: {headers}')
    print(f'Params: {params}')

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text[:200]}...')
    except Exception as e:
        print(f'Erreur: {e}')

elif method == 'token':
    # Test méthode TOKEN
    url = 'https://www.aqilas.com/api/v1/sms'
    headers = {'X-AUTH-TOKEN': token, 'Content-Type': 'application/json'}
    payload = {'contacts': '22670000000', 'senderid': 'NOTAIRE', 'msg': 'Test OTP: 123456'}

    print(f'Test URL: {url}')
    print(f'Headers: {headers}')
    print(f'Payload: {payload}')

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text[:200]}...')
    except Exception as e:
        print(f'Erreur: {e}')