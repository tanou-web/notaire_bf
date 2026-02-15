# 🧪 GUIDE DE TEST COMPLET - NOTAIRES BF

## 🚀 **PRÉPARATION AVANT LES TESTS**

### **1. Vérifier que le serveur Django tourne**

```bash
# Démarrer le serveur si ce n'est pas déjà fait
python manage.py runserver
```

**Vérification :** Ouvrir `http://localhost:8000/admin/` dans le navigateur

### **2. Vérifier la configuration SMS**

```bash
python manage.py shell
```

```python
from django.conf import settings
print(f"AQILAS_TOKEN: {'DEFINI' if getattr(settings, 'AQILAS_TOKEN', None) else 'NON DEFINI'}")
print(f"AQILAS_SENDER: {getattr(settings, 'AQILAS_SENDER', 'NON DEFINI')}")
```

---

## 📋 **TEST 1 : GÉNÉRATION TOKEN JWT (LOGIN)**

### **Objectif :** Vérifier que les tokens JWT sont générés lors du login

### **Créer un utilisateur de test (si nécessaire)**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

user, created = User.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'test@example.com',
        'nom': 'Test',
        'prenom': 'User',
        'telephone': '+22670000000',
        'email_verifie': True,
        'telephone_verifie': True
    }
)
if created:
    user.set_password('Test123!@#')
    user.is_active = True
    user.save()
    print('✅ Utilisateur créé')
else:
    print('✅ Utilisateur existe déjà')
    user.set_password('Test123!@#')
    user.save()
```

### **Test avec curl**

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"testuser\",
    \"password\": \"Test123!@#\"
  }"
```

### **Résultat attendu :**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### **✅ Validation :**
- ✅ Code HTTP : **200 OK**
- ✅ Présence de `refresh` token
- ✅ Présence de `access` token
- ✅ Tokens sont des strings JWT valides

---

## 📱 **TEST 2 : INSCRIPTION ET ENVOI SMS OTP**

### **Objectif :** Vérifier que l'inscription génère un OTP et l'envoie par SMS

### **Test avec curl**

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"nouveau_user\",
    \"email\": \"nouveau@example.com\",
    \"telephone\": \"+22670000000\",
    \"password\": \"Nouveau123!@#\",
    \"password_confirmation\": \"Nouveau123!@#\",
    \"nom\": \"Nouveau\",
    \"prenom\": \"User\",
    \"accept_terms\": true
  }"
```

### **Résultat attendu :**

```json
{
  "message": "Inscription réussie. Un code de vérification a été envoyé par SMS à votre numéro de téléphone.",
  "user_id": 2,
  "telephone": "+22670000000",
  "next_step": "verify_telephone"
}
```

### **Vérifier en base de données**

```bash
python manage.py shell
```

```python
from apps.utilisateurs.models import VerificationVerificationtoken
from apps.communications.models import CommunicationsSmslog

# Voir le dernier token OTP créé
last_token = VerificationVerificationtoken.objects.last()
print(f"User: {last_token.user.username}")
print(f"Type: {last_token.type_token}")
print(f"Expire: {last_token.expires_at}")
print(f"Utilisé: {last_token.used}")

# Voir le dernier SMS envoyé
last_sms = CommunicationsSmslog.objects.last()
print(f"\nSMS:")
print(f"Destinataire: {last_sms.destinataire}")
print(f"Statut: {last_sms.statut}")  # Doit être 'envoye' ou 'echec'
print(f"Message ID: {last_sms.message_id}")
print(f"Erreur: {last_sms.erreur}")
```

### **✅ Validation :**
- ✅ Code HTTP : **201 Created**
- ✅ Message de confirmation présent
- ✅ Token OTP créé en base (`VerificationVerificationtoken`)
- ✅ Log SMS créé (`CommunicationsSmslog`)
- ✅ Statut SMS : `envoye` ou `echec` (vérifier l'erreur si `echec`)

---

## 🔐 **TEST 3 : VÉRIFICATION OTP**

### **Objectif :** Vérifier que le code OTP peut être vérifié

### **Récupérer le token OTP**

**Option A : Si vous avez reçu le SMS**
- Utiliser le code reçu (ex: "123456")

**Option B : Récupérer depuis la base (pour les tests)**

```bash
python manage.py shell
```

```python
from apps.utilisateurs.models import VerificationVerificationtoken, User
from apps.utilisateurs.security.token_generator import VerificationTokenGenerator

# Trouver l'utilisateur
user = User.objects.get(username='nouveau_user')

# Créer un token de test (attention: le hash est différent, donc il faut utiliser le vrai token)
# Pour les tests, on peut vérifier directement en base
token_obj = VerificationVerificationtoken.objects.filter(
    user=user,
    type_token='telephone',
    used=False
).first()

if token_obj:
    print(f"Token trouvé (hashé): {token_obj.token[:20]}...")
    print("Pour tester, utilisez le code OTP reçu par SMS")
else:
    print("Aucun token trouvé - relancer l'inscription")
```

### **Test de vérification (avec le vrai code reçu)**

```bash
curl -X POST http://localhost:8000/api/auth/verify-token/ \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"123456\",
    \"verification_type\": \"sms\",
    \"telephone\": \"+22670000000\"
  }"
```

### **Résultat attendu (succès) :**

```json
{
  "message": "Code de vérification validé avec succès",
  "user_id": 2,
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "nouveau_user",
    "email": "nouveau@example.com",
    ...
  }
}
```

### **✅ Validation :**
- ✅ Code HTTP : **200 OK**
- ✅ Message de succès
- ✅ Tokens JWT présents (`access` et `refresh`)
- ✅ User activé (`is_active = True`)
- ✅ Téléphone vérifié (`telephone_verifie = True`)

---

## 🔄 **TEST 4 : ENVOI SMS (SANS INSCRIPTION)**

### **Objectif :** Tester l'envoi SMS directement

### **Test d'envoi de vérification**

```bash
curl -X POST http://localhost:8000/api/auth/send-verification/ \
  -H "Content-Type: application/json" \
  -d "{
    \"verification_type\": \"sms\",
    \"telephone\": \"+22670000000\"
  }"
```

### **Résultat attendu :**

```json
{
  "message": "Un code de vérification a été envoyé",
  "token_id": 5,
  "expires_at": "2024-01-XX..."
}
```

### **Vérifier les logs SMS**

```bash
python manage.py shell
```

```python
from apps.communications.models import CommunicationsSmslog

# Voir tous les SMS envoyés
sms_logs = CommunicationsSmslog.objects.all().order_by('-created_at')[:5]

for sms in sms_logs:
    print(f"Date: {sms.created_at}")
    print(f"Destinataire: {sms.destinataire}")
    print(f"Statut: {sms.statut}")
    print(f"Message ID: {sms.message_id}")
    print(f"Erreur: {sms.erreur}")
    print("-" * 50)
```

---

## 🧪 **TEST 5 : SCRIPT DE TEST AUTOMATISÉ**

### **Créer un script Python complet**

```python
# test_complet.py
import requests
import json

BASE_URL = "http://localhost:8000"

def test_inscription_complete():
    """Test complet : Inscription → Vérification OTP → Login"""
    
    print("=== TEST INSCRIPTION COMPLÈTE ===\n")
    
    # 1. Inscription
    print("1. Inscription...")
    register_data = {
        "username": "test_complet",
        "email": "testcomplet@example.com",
        "telephone": "+22670000000",
        "password": "Test123!@#",
        "password_confirmation": "Test123!@#",
        "nom": "Test",
        "prenom": "Complet",
        "accept_terms": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/register/",
        json=register_data
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 201:
        print("   ✅ Inscription réussie")
        
        # 2. Vérifier qu'un SMS a été envoyé
        print("\n2. Vérification envoi SMS...")
        # (Vérifier en base de données)
        
        # 3. Vérification OTP (nécessite le vrai code)
        print("\n3. Vérification OTP...")
        print("   ⚠️ Entrez le code reçu par SMS dans votre terminal")
        otp_code = input("   Code OTP: ")
        
        verify_data = {
            "token": otp_code,
            "verification_type": "sms",
            "telephone": register_data["telephone"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-token/",
            json=verify_data
        )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200 and "access" in result:
            print("   ✅ Vérification réussie")
            print(f"   Access Token: {result['access'][:50]}...")
            
            # 4. Login avec tokens
            print("\n4. Test login avec tokens...")
            headers = {"Authorization": f"Bearer {result['access']}"}
            response = requests.get(
                f"{BASE_URL}/api/auth/users/me/",
                headers=headers
            )
            
            if response.status_code == 200:
                print("   ✅ Login réussi avec token")
                print(f"   User: {response.json()}")
        else:
            print(f"   ❌ Erreur: {result}")
    else:
        print(f"   ❌ Erreur inscription: {response.json()}")

if __name__ == "__main__":
    test_inscription_complete()
```

### **Exécuter le script**

```bash
python test_complet.py
```

---

## 📊 **TEST 6 : VÉRIFIER LES LOGS D'AUDIT**

### **Vérifier que tout est journalisé**

```bash
python manage.py shell
```

```python
from apps.audit.models import SecurityLog, LoginAttemptLog

# Voir les tentatives de login
logins = LoginAttemptLog.objects.all().order_by('-timestamp')[:10]
for login in logins:
    print(f"{login.timestamp}: {login.username} - {login.success} - {login.ip_address}")

# Voir les événements de sécurité
security = SecurityLog.objects.all().order_by('-timestamp')[:10]
for event in security:
    print(f"{event.timestamp}: {event.action} - {event.user}")
```

---

## 🔍 **TEST 7 : VÉRIFIER LES ERREURS POSSIBLES**

### **Test avec mauvais identifiants**

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "inexistant",
    "password": "mauvais"
  }'
```

**Résultat attendu :** `401 Unauthorized` avec message d'erreur

### **Test avec OTP invalide**

```bash
curl -X POST http://localhost:8000/api/auth/verify-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "000000",
    "verification_type": "sms",
    "telephone": "+22670000000"
  }'
```

**Résultat attendu :** `400 Bad Request` avec message d'erreur

---

## 📋 **CHECKLIST DE VALIDATION FINALE**

### **✅ Tests à valider :**

- [ ] **Login réussit** et retourne tokens JWT
- [ ] **Inscription crée** un utilisateur
- [ ] **Token OTP généré** et sauvegardé en base
- [ ] **SMS envoyé** (statut `envoye` dans `CommunicationsSmslog`)
- [ ] **Code OTP vérifié** avec succès
- [ ] **User activé** après vérification OTP
- [ ] **Tokens JWT retournés** après vérification OTP
- [ ] **Login fonctionne** avec le token JWT
- [ ] **Logs d'audit** créés pour toutes les actions
- [ ] **Rate limiting** fonctionne (tester avec plusieurs tentatives)

---

## 🆘 **RÉSOUDRE LES PROBLÈMES COURANTS**

### **Problème 1 : SMS non envoyé (statut = 'echec')**

**Vérifier :**
```python
from apps.communications.models import CommunicationsSmslog
last_sms = CommunicationsSmslog.objects.last()
print(f"Erreur: {last_sms.erreur}")
```

**Solutions possibles :**
- Vérifier que `AQILAS_TOKEN` est valide
- Vérifier les crédits SMS sur votre compte Aqilas
- Vérifier le format du numéro (+226XXXXXXXXX)
- Vérifier que l'API Aqilas est accessible

### **Problème 2 : Token OTP non trouvé**

**Vérifier :**
```python
from apps.utilisateurs.models import VerificationVerificationtoken
tokens = VerificationVerificationtoken.objects.filter(used=False)
print(f"Tokens actifs: {tokens.count()}")
```

### **Problème 3 : Tokens JWT non générés**

**Vérifier :**
- L'utilisateur est actif (`is_active = True`)
- L'email est vérifié (`email_verifie = True`)
- Les credentials sont corrects

---

## 🎯 **RÉSUMÉ DES COMMANDES IMPORTANTES**

```bash
# 1. Inscription
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", ...}'

# 2. Vérification OTP
curl -X POST http://localhost:8000/api/auth/verify-token/ \
  -H "Content-Type: application/json" \
  -d '{"token": "123456", "verification_type": "sms", ...}'

# 3. Login
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "Test123!@#"}'

# 4. Vérifier profil (avec token)
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/auth/users/me/
```

---

**Votre système est maintenant prêt à être testé !** 🧪✨
