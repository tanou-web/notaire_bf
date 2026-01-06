# 🔄 GUIDE DE GESTION DES TOKENS JWT

## 🎯 **PROBLÈME : Token expiré**
```
Erreur: Given token not valid for any token type
Détails: {"detail":"Given token not valid for any token type","code":"token_not_valid","messages":[{"token_class":"AccessToken","token_type":"access","message":"Token is expired"}]}
```

---

## ✅ **SOLUTIONS IMPLEMENTÉES**

### 1. **Durée de vie prolongée des tokens**
```python
# notaires_bf/settings/base.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),    # 60min → 2h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # 1j → 7j
    'ROTATE_REFRESH_TOKENS': True,                  # Rotation auto
}
```

### 2. **Middleware de rafraîchissement automatique**
```python
# notaires_bf/middleware.py - Nouveau middleware
class JWTTokenRefreshMiddleware:
    """Gère automatiquement le rafraîchissement des tokens expirés"""
```

### 3. **Endpoint de vérification ajouté**
```python
# notaires_bf/urls.py
path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify')
```

---

## 🔧 **UTILISATION POUR LES DÉVELOPPEURS FRONTEND**

### **Endpoints disponibles :**
```javascript
// 1. Obtenir un nouveau token
POST /api/token/
{
  "username": "user",
  "password": "pass"
}

// 2. Rafraîchir un token
POST /api/token/refresh/
{
  "refresh": "your_refresh_token"
}

// 3. Vérifier un token (NOUVEAU)
POST /api/token/verify/
{
  "token": "your_access_token"
}
```

### **Gestion automatique dans le frontend :**
```javascript
// Intercepteur Axios pour gérer les tokens expirés
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 &&
        error.response?.data?.code === 'token_not_valid') {

      // Tenter de rafraîchir automatiquement
      return refreshToken()
        .then(() => {
          // Retry la requête originale
          return axios(error.config);
        })
        .catch(() => {
          // Redirection vers login si échec
          redirectToLogin();
        });
    }
    return Promise.reject(error);
  }
);
```

---

## 📊 **NOUVELLES DURÉES DE VIE**

| Token | Avant | Après | Amélioration |
|-------|-------|-------|-------------|
| **Access** | 60 minutes | **2 heures** | +100% |
| **Refresh** | 1 jour | **7 jours** | +600% |

---

## 🔄 **FLUX DE TRAVAIL RECOMMANDÉ**

1. **Connexion** → Recevoir access + refresh tokens
2. **Utiliser access token** pour les requêtes API
3. **Si 401/token_not_valid** → Rafraîchir automatiquement
4. **Si refresh échoue** → Redemander la connexion

---

## ⚠️ **POINTS IMPORTANTS**

- ✅ **Tokens plus longs** = Moins de reconnexions
- ✅ **Rotation automatique** = Sécurité renforcée
- ✅ **Middleware intelligent** = Gestion transparente
- ✅ **Endpoint verify** = Vérification manuelle possible

**Résultat : Expérience utilisateur fluide avec sécurité maintenue !** 🚀
