# 📚 DOCUMENTATION API - Guide pour le Développeur Frontend

## 🌐 URL de Base

```
http://localhost:8000/api/  (Développement)
https://votre-domaine.com/api/  (Production)
```

## 🔐 Authentification

L'API utilise **JWT (JSON Web Tokens)** pour l'authentification.

### Obtenir un token JWT
```http
POST /api/token/
Content-Type: application/json

{
  "username": "votre_username",
  "password": "votre_password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Utiliser le token
Ajoutez dans les headers de vos requêtes :
```
Authorization: Bearer <votre_access_token>
```

### Rafraîchir le token
```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "votre_refresh_token"
}
```

---

## 📋 ENDPOINTS PAR CATÉGORIE

## 1️⃣ AUTHENTIFICATION (`/api/auth/`)

### 🔑 Connexion
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}

Response 200:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "nom": "Admin",
    "prenom": "User"
  }
}
```

### 🚪 Déconnexion
```http
POST /api/auth/logout/
Authorization: Bearer <token>
Content-Type: application/json

{
  "refresh": "votre_refresh_token"
}
```



### ✉️ Envoyer code de vérification
```http
POST /api/auth/send-verification/
Content-Type: application/json

{
  "email": "user@example.com",
  "type": "email"  // ou "telephone"
}
```

### ✔️ Vérifier le code
```http
POST /api/auth/verify-token/
Content-Type: application/json

{
  "token": "123456",
  "type": "email"
}
```

### 🔄 Renvoyer le code
```http
POST /api/auth/resend-verification/
Content-Type: application/json

{
  "email": "user@example.com",
  "type": "email"
}
```

### 🔑 Réinitialiser le mot de passe
```http
POST /api/auth/password-reset/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### 🔒 Changer le mot de passe (utilisateur connecté)
```http
PUT /api/auth/password-change/
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "ancien_mdp",
  "new_password": "nouveau_mdp",
  "new_password_confirmation": "nouveau_mdp"
}
```

### 👨‍💼 Créer un administrateur (superuser seulement)
```http
POST /api/auth/create-admin/
Authorization: Bearer <superuser_token>
Content-Type: application/json

{
  "username": "new_admin",
  "email": "admin@example.com",
  "password": "secure_password123",
  "password_confirmation": "secure_password123",
  "nom": "Admin",
  "prenom": "User",
  "telephone": "+22670123456",
  "is_staff": true,
  "is_superuser": true
}
```

---

## 2️⃣ ORGANISATION (`/api/organisation/`)

### 📊 Statistiques du bureau
```http
GET /api/organisation/stats/
Authorization: Bearer <admin_token>

Response 200:
{
  "total_membres": 15,
  "membres_actifs": 12,
  "membres_en_mandat": 10,
  "repartition_par_poste": {
    "Président": 1,
    "Vice-Président": 1,
    "Secrétaire": 1
  },
  "anciennete_moyenne": 5.2
}
```

### 🏛️ Bureau public
```http
GET /api/organisation/bureau/

Response 200:
{
  "Président": [
    {
      "id": 1,
      "nom": "Dupont",
      "prenom": "Jean",
      "poste": "president",
      "photo": "/media/membres_bureau/photo.jpg"
    }
  ],
  "Vice-Président": [...],
  "Secrétaire": [...]
}
```

### 📚 Historique de l'Ordre
```http
GET /api/organisation/historique/

Response 200:
[
  {
    "id": 1,
    "titre": "Création de l'Ordre",
    "contenu": "L'Ordre a été créé en...",
    "date_evenement": "1990-01-15",
    "ordre": 1,
    "image": "/media/historique/image.jpg",
    "actif": true
  }
]

POST /api/organisation/historique/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "titre": "Nouvel événement",
  "contenu": "Description...",
  "date_evenement": "2024-01-15",
  "ordre": 2,
  "actif": true
}
```

### 🎯 Missions de l'Ordre
```http
GET /api/organisation/missions/

Response 200:
[
  {
    "id": 1,
    "titre": "Mission 1",
    "description": "Description de la mission",
    "icone": "fas fa-gavel",
    "ordre": 1,
    "actif": true
  }
]

POST /api/organisation/missions/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "titre": "Nouvelle mission",
  "description": "Description...",
  "icone": "fas fa-shield-alt",
  "ordre": 1,
  "actif": true
}
```

### 👥 Membres du bureau

#### Liste complète
```http
GET /api/organisation/membres-bureau/
GET /api/organisation/membres-bureau/?poste=president
GET /api/organisation/membres-bureau/?actif=true
GET /api/organisation/membres-bureau/?search=dupont
```

#### Membres en mandat
```http
GET /api/organisation/membres-bureau/en-mandat/

Response 200:
[
  {
    "id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "poste": "president",
    "photo": "/media/...",
    "mot_du_president": "Message du président..."
  }
]
```

#### Membres par poste
```http
GET /api/organisation/membres-bureau/par-poste/

Response 200:
{
  "Président": [
    {"id": 1, "nom": "Dupont", "prenom": "Jean", ...}
  ],
  "Vice-Président": [...],
  "Secrétaire": [...]
}
```

#### Bureau exécutif
```http
GET /api/organisation/membres-bureau/bureau-executif/
```

#### Créer un membre (admin)
```http
POST /api/organisation/membres-bureau/
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

{
  "nom": "Nom",
  "prenom": "Prénom",
  "poste": "president",
  "photo": <file>,
  "telephone": "+22670123456",
  "email": "email@example.com",
  "biographie": "Biographie...",
  "mot_du_president": "Message du président",
  "ordre": 1,
  "actif": true
}
```

#### Activer/Désactiver un membre (admin)
```http
POST /api/organisation/membres-bureau/1/activer/
Authorization: Bearer <admin_token>

POST /api/organisation/membres-bureau/1/desactiver/
Authorization: Bearer <admin_token>
```

---

## 3️⃣ NOTAIRES (`/api/notaires/`)

### 📋 Liste des notaires
```http
GET /api/notaires/notaires/
GET /api/notaires/notaires/?region=ouagadougou
GET /api/notaires/notaires/?ville=ouaga
GET /api/notaires/notaires/?search=dupont
GET /api/notaires/notaires/?actif=true

Response 200:
[
  {
    "id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "telephone": "+22670123456",
    "adresse": "123 Rue...",
    "region": "Ouagadougou",
    "ville": "Ouagadougou",
    "photo": "/media/notaires/photo.jpg",
    "actif": true
  }
]
```

### ➕ Créer un notaire (admin)
```http
POST /api/notaires/notaires/
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

{
  "nom": "Nom",
  "prenom": "Prénom",
  "email": "email@example.com",
  "telephone": "+22670123456",
  "adresse": "Adresse complète",
  "region": "Ouagadougou",
  "ville": "Ouagadougou",
  "photo": <file>,
  "actif": true
}
```

---

## 4️⃣ DOCUMENTS (`/api/documents/`)

### 📄 Liste des documents
```http
GET /api/documents/documents/
GET /api/documents/documents/?actif=true
GET /api/documents/documents/?search=acte

Response 200:
[
  {
    "id": 1,
    "titre": "Acte de naissance",
    "description": "Description du document",
    "prix": 5000.00,
    "delai_traitement": 48,
    "actif": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### ➕ Créer un document (admin)
```http
POST /api/documents/documents/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "titre": "Nouveau document",
  "description": "Description...",
  "prix": 10000.00,
  "delai_traitement": 72,
  "actif": true
}
```

### 📜 Textes légaux
```http
GET /api/documents/textes-legaux/

Response 200:
[
  {
    "id": 1,
    "titre": "Loi sur les notaires",
    "contenu": "Texte complet...",
    "type": "loi",
    "date_publication": "2020-01-15",
    "fichier": "/media/textes/loi.pdf"
  }
]
```

---

## 5️⃣ DEMANDES (`/api/demandes/`)

### 📝 Liste des demandes
```http
GET /api/demandes/demandes/
Authorization: Bearer <token>
GET /api/demandes/demandes/?statut=en_attente_traitement
GET /api/demandes/demandes/?utilisateur=1

Response 200:
[
  {
    "id": 1,
    "reference": "DEM-2024-001",
    "statut": "en_attente_traitement",
    "document": {
      "id": 1,
      "titre": "Acte de naissance"
    },
    "montant_total": 5000.00,
    "frais_commission": 150.00,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### ➕ Créer une demande
```http
POST /api/demandes/demandes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "document": 1,
  "email_reception": "client@example.com",
  "donnees_formulaire": {
    "nom": "Dupont",
    "prenom": "Jean",
    "date_naissance": "1990-01-15",
    "lieu_naissance": "Ouagadougou"
  }
}

Response 201:
{
  "id": 1,
  "reference": "DEM-2024-001",
  "statut": "attente_formulaire",
  "montant_total": 5000.00,
  "frais_commission": 150.00
}
```

### 📎 Pièces jointes
```http
GET /api/demandes/pieces-jointes/
Authorization: Bearer <token>
GET /api/demandes/pieces-jointes/?demande=1

POST /api/demandes/pieces-jointes/
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "demande": 1,
  "type_piece": "cnib",
  "fichier": <file>,
  "description": "CNIB recto-verso"
}

Response 201:
{
  "id": 1,
  "type_piece": "cnib",
  "fichier": "/media/demandes/pieces_jointes/2024/01/cnib.pdf",
  "nom_original": "cnib.pdf",
  "taille_fichier": 524288,
  "taille_formatee": "512.00 KB"
}
```

---

## 6️⃣ PAIEMENTS (`/api/paiements/`)

### 💳 Transactions
```http
GET /api/paiements/transactions/
Authorization: Bearer <token>
GET /api/paiements/transactions/?statut=validee

Response 200:
[
  {
    "id": 1,
    "reference": "PAY-2024-001",
    "type_paiement": "orange_money",
    "montant": 5000.00,
    "commission": 150.00,
    "statut": "validee",
    "date_creation": "2024-01-15T10:00:00Z",
    "date_validation": "2024-01-15T10:05:00Z"
  }
]
```

### ➕ Créer une transaction
```http
POST /api/paiements/transactions/
Authorization: Bearer <token>
Content-Type: application/json

{
  "demande": 1,
  "type_paiement": "orange_money",
  "montant": 5000.00
}

Response 201:
{
  "id": 1,
  "reference": "PAY-2024-001",
  "statut": "initiee",
  "url_paiement": "https://payment-gateway.com/..."
}
```

---

## 7️⃣ ACTUALITÉS (`/api/actualites/`)

```http
GET /api/actualites/actualites/
GET /api/actualites/actualites/?publie=true
GET /api/actualites/actualites/?categorie=communique
GET /api/actualites/actualites/?featured=true

Response 200:
[
  {
    "id": 1,
    "titre": "Titre de l'actualité",
    "slug": "titre-actualite",
    "contenu": "Contenu complet...",
    "resume": "Résumé...",
    "categorie": "communique",
    "image_principale": "/media/actualites/image.jpg",
    "date_publication": "2024-01-15T10:00:00Z",
    "important": false,
    "publie": true,
    "featured": true
  }
]

POST /api/actualites/actualites/
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

{
  "titre": "Nouvelle actualité",
  "contenu": "Contenu...",
  "resume": "Résumé...",
  "categorie": "communique",
  "image_principale": <file>,
  "publie": true,
  "important": false,
  "featured": false
}
```

---

## 8️⃣ CONSEILS (`/api/conseils/`)

```http
GET /api/conseils/conseils/
GET /api/conseils/conseils/?actif=true

Response 200:
[
  {
    "id": 1,
    "titre": "Conseil du jour",
    "contenu": "Contenu du conseil...",
    "date_publication": "2024-01-15",
    "actif": true
  }
]
```

---

## 9️⃣ GÉOGRAPHIE (`/api/geographie/`)

### Régions
```http
GET /api/geographie/regions/

Response 200:
[
  {
    "id": 1,
    "nom": "Ouagadougou",
    "code": "OUA"
  }
]
```

### Villes
```http
GET /api/geographie/villes/
GET /api/geographie/villes/?region=1

Response 200:
[
  {
    "id": 1,
    "nom": "Ouagadougou",
    "region": {
      "id": 1,
      "nom": "Ouagadougou"
    }
  }
]
```

---

## 🔟 CONTACT (`/api/contact/`)

### Informations de contact
```http
GET /api/contact/info/

Response 200:
{
  "adresse": "123 Rue...",
  "telephone": "+22670123456",
  "email": "contact@notaires.bf",
  "latitude": 12.3714,
  "longitude": -1.5197,
  "facebook": "https://facebook.com/...",
  "linkedin": "https://linkedin.com/...",
  "tiktok": "https://tiktok.com/..."
}
```

### Formulaire de contact
```http
POST /api/contact/form/
Content-Type: application/json

{
  "nom": "Dupont",
  "email": "dupont@example.com",
  "sujet": "Question",
  "message": "Message..."
}

Response 201:
{
  "message": "Votre message a été envoyé avec succès"
}
```

---

## 1️⃣1️⃣ STATISTIQUES (`/api/stats/`)

```http
GET /api/stats/visites/
GET /api/stats/pages/
GET /api/stats/referents/
GET /api/stats/pays/
GET /api/stats/periodes/
Authorization: Bearer <admin_token>
```

---

## 1️⃣2️⃣ VENTES (`/api/ventes/`)

```http
GET /api/ventes/stickers/
Authorization: Bearer <token>

POST /api/ventes/stickers/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "notaire": 1,
  "quantite": 100,
  "montant_total": 50000.00
}
```

---

## 1️⃣3️⃣ SYSTÈME (`/api/system/`)

### Emails professionnels (admin seulement)
```http
GET /api/system/emails-professionnels/
Authorization: Bearer <admin_token>

POST /api/system/emails-professionnels/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "contact1@notaires.bf",
  "mot_de_passe": "password123",
  "actif": true
}
```

---

## 1️⃣4️⃣ CORE (`/api/core/`)

### Pages CMS
```http
GET /api/core/pages/
GET /api/core/pages/slug-de-la-page/

Response 200:
{
  "id": 1,
  "titre": "À propos",
  "slug": "a-propos",
  "contenu": "Contenu de la page...",
  "publie": true
}

POST /api/core/pages/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "titre": "Nouvelle page",
  "slug": "nouvelle-page",
  "contenu": "Contenu...",
  "publie": true
}
```

### Configurations
```http
GET /api/core/configurations/
Authorization: Bearer <admin_token>
```

---

## 📝 NOTES IMPORTANTES POUR LE FRONTEND

### 1. **Gestion des erreurs**
Toutes les erreurs suivent ce format :
```json
{
  "error": "Message d'erreur",
  "detail": "Détails supplémentaires"
}
```

Codes HTTP :
- `200` : Succès
- `201` : Créé avec succès
- `400` : Erreur de validation
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Non trouvé
- `500` : Erreur serveur

### 2. **Pagination**
Les endpoints de liste utilisent la pagination :
```json
{
  "count": 100,
  "next": "http://api.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### 3. **Filtres et recherche**
Utilisez les query parameters :
- `?search=terme` : Recherche
- `?ordering=nom` : Tri
- `?page=1` : Pagination
- `?actif=true` : Filtres spécifiques

### 4. **Upload de fichiers**
Pour les endpoints avec upload (photo, pièces jointes) :
- Utilisez `multipart/form-data`
- Limite : 10 MB par fichier
- Formats acceptés : PDF, JPG, PNG

### 5. **CORS**
L'API accepte les requêtes depuis n'importe quelle origine (configuré dans le backend).

---

## 🧪 TESTER L'API

### Swagger Documentation
Accédez à : `http://localhost:8000/swagger/`

### ReDoc Documentation
Accédez à : `http://localhost:8000/redoc/`

---

## 📞 SUPPORT

Pour toute question, contactez l'équipe backend.

**Documentation générée le :** $(date)

