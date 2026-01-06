# 🌐 GUIDE DE CONFIGURATION CORS - FRONTEND

## 🎯 **PROBLÈME RÉSOLU**
Erreur CORS résolue côté Django ! Maintenant configurez votre frontend.

---

## ✅ **CONFIGURATION DJANGO (DÉJÀ FAITE)**

### **Settings optimisés :**
```python
# Développement
CORS_ALLOW_ALL_ORIGINS = True  # Permissif en dev
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',   # React
    'http://localhost:5173',   # Vite
    'http://localhost:8080',   # Vue/Angular
]

# Headers autorisés
CORS_ALLOW_HEADERS = ['authorization', 'content-type', ...]
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_ALLOW_CREDENTIALS = True
```

---

## 🔧 **CONFIGURATION PAR FRAMEWORK**

### **⚛️ REACT - Axios**
```javascript
// src/api/config.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true,  // IMPORTANT pour les cookies
  headers: {
    'Content-Type': 'application/json',
  }
});

// Intercepteur pour les tokens
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Gestion des erreurs 401 (token expiré)
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 &&
        error.response?.data?.code === 'token_not_valid') {

      // Rafraîchir le token automatiquement
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('http://localhost:8000/api/token/refresh/', {
          refresh: refreshToken
        });

        // Sauvegarder le nouveau token
        localStorage.setItem('access_token', response.data.access);

        // Retry la requête originale
        error.config.headers.Authorization = `Bearer ${response.data.access}`;
        return axios(error.config);

      } catch (refreshError) {
        // Échec du refresh - déconnexion
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

### **🟡 VUE.JS - Axios**
```javascript
// src/plugins/axios.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Intercepteur requête
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur réponse
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 &&
        error.response?.data?.code === 'token_not_valid') {

      return axios.post('http://localhost:8000/api/token/refresh/', {
        refresh: localStorage.getItem('refresh_token')
      }).then(response => {
        localStorage.setItem('access_token', response.data.access);
        error.config.headers.Authorization = `Bearer ${response.data.access}`;
        return axios(error.config);
      }).catch(() => {
        localStorage.clear();
        window.location.href = '/login';
      });
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### **🎯 ANGULAR - HttpClient**
```typescript
// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';
  private refreshTokenSubject = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    });
  }

  get<T>(endpoint: string): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      catchError(error => this.handleError(error, () => this.get<T>(endpoint)))
    );
  }

  post<T>(endpoint: string, data: any): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, data, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      catchError(error => this.handleError(error, () => this.post<T>(endpoint, data)))
    );
  }

  private handleError(error: HttpErrorResponse, retryFn: () => Observable<any>): Observable<any> {
    if (error.status === 401 &&
        error.error?.code === 'token_not_valid' &&
        !error.url?.includes('/token/refresh/')) {

      return this.refreshToken().pipe(
        switchMap(() => retryFn())
      );
    }
    return throwError(error);
  }

  private refreshToken(): Observable<any> {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) {
      this.logout();
      return throwError('No refresh token');
    }

    return this.http.post(`${this.baseUrl}/token/refresh/`, { refresh }).pipe(
      catchError(() => {
        this.logout();
        return throwError('Refresh failed');
      })
    );
  }

  private logout() {
    localStorage.clear();
    window.location.href = '/login';
  }
}
```

---

## 🧪 **TEST DE VALIDATION**

### **Script de test rapide :**
```javascript
// test-cors.html
<!DOCTYPE html>
<html>
<head>
    <title>Test CORS</title>
</head>
<body>
    <h1>Test CORS API</h1>
    <button onclick="testAPI()">Tester l'API</button>
    <div id="result"></div>

    <script>
        async function testAPI() {
            const result = document.getElementById('result');

            try {
                // Test endpoint public
                const response = await fetch('http://localhost:8000/api/geographie/regions/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    const data = await response.json();
                    result.innerHTML = `
                        <h2>✅ SUCCÈS CORS !</h2>
                        <p>Status: ${response.status}</p>
                        <p>Data reçue: ${JSON.stringify(data, null, 2)}</p>
                    `;
                } else {
                    result.innerHTML = `<h2>❌ ERREUR HTTP: ${response.status}</h2>`;
                }
            } catch (error) {
                result.innerHTML = `<h2>❌ ERREUR CORS: ${error.message}</h2>`;
            }
        }
    </script>
</body>
</html>
```

### **Commandes de test :**
```bash
# Tester l'API directement
curl -H "Content-Type: application/json" http://localhost:8000/api/geographie/regions/

# Tester avec credentials
curl -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -X GET http://localhost:8000/api/notaires/notaires/
```

---

## 🚀 **DÉPLOIEMENT EN PRODUCTION**

### **Variables d'environnement :**
```bash
# .env.production
CORS_ALLOWED_ORIGINS=https://votredomaine.com,https://www.votredomaine.com
DEBUG=False
```

### **Configuration production :**
```python
# settings/production.py
CORS_ALLOWED_ORIGINS = [
    'https://votredomaine.com',
    'https://api.votredomaine.com',
]
CORS_ALLOW_ALL_ORIGINS = False
```

---

## 🔍 **DÉBOGAGE CORS**

### **Headers à vérifier :**
```
✅ Access-Control-Allow-Origin: http://localhost:3000
✅ Access-Control-Allow-Credentials: true
✅ Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
✅ Access-Control-Allow-Headers: authorization, content-type
```

### **Outils de debug :**
- **Navigateur** : Onglet Network → Headers de réponse
- **Console** : Erreurs CORS détaillées
- **Postman** : Tester les endpoints directement

---

## ✅ **RÉSULTAT ATTENDU**

Après configuration :
- ✅ **Console** : `[API] ✅ Succès` au lieu d'erreur CORS
- ✅ **Données** : Conseils et actualités s'affichent
- ✅ **Auth** : Tokens JWT fonctionnent correctement
- ✅ **Performance** : Rafraîchissement automatique des tokens

**🎉 CORS configuré - API prête pour le frontend !**
