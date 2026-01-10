#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from django.conf import settings

print('=== VERIFICATION CONFIGURATION SMS ===')
api_key = getattr(settings, 'AQILAS_API_KEY', None)
token = getattr(settings, 'AQILAS_TOKEN', None)

print('AQILAS_API_KEY:', api_key)
print('AQILAS_TOKEN:', 'DEFINI' if token else 'NON DEFINI')

if api_key and api_key != 'votre-cle-api-aqilas':
    print('Methode utilisee: API_KEY/API_SECRET')
    method = 'api_key'
else:
    print('Methode utilisee: TOKEN direct')
    method = 'token'

print('\n=== TEST PARAMETRES ===')
test_phone = "66342505"
test_otp = "123456"

if method == 'token':
    # Format token
    if test_phone.startswith('+'):
        phone_number = test_phone[1:]
    else:
        phone_number = test_phone

    if not phone_number.startswith('226'):
        phone_number = f"226{phone_number}"

    payload = {
        "contacts": phone_number,
        "senderid": getattr(settings, 'AQILAS_SENDER', 'NOTAIRE'),
        "msg": f"Votre code OTP est : {test_otp}"
    }

    headers = {
        "X-AUTH-TOKEN": token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    url = "https://www.aqilas.com/api/v1/sms"

else:
    # Format API_KEY
    if not test_phone.startswith('+'):
        phone_number = f"+{test_phone}"
    else:
        phone_number = test_phone

    params = {
        "to": phone_number,
        "message": f"Votre code OTP est : {test_otp}",
        "from": getattr(settings, 'AQILAS_SENDER_ID', 'NOTAIRES')
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    url = "https://www.aqilas.com/api/v1/sms/send"

print(f'URL: {url}')
print(f'Headers: {headers}')
if method == 'token':
    print(f'Payload: {payload}')
else:
    print(f'Params: {params}')

print('\n=== TEST REEL ===')
import requests

try:
    if method == 'token':
        response = requests.post(url, json=payload, headers=headers, timeout=10)
    else:
        response = requests.get(url, headers=headers, params=params, timeout=10)

    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')

except Exception as e:
    print(f'Erreur: {e}')