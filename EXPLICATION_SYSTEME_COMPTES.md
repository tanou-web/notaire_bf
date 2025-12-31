
## TYPES D'UTILISATEURS

###  **Administrateurs** (avec compte obligatoire)
- **Qui** : Membres de l'Ordre des Notaires (personnel administratif)
- **Compte** : ✅ **OBLIGATOIRE** - Doivent créer un compte
- **Accès** : Back-office complet
- **Permissions** : Peuvent :
  - ✅ Voir toutes les demandes et ventes
  - ✅ Suivre les statistiques de ventes
  - ✅ Gérer les documents payants
  - ✅ Assigner des demandes aux notaires
  - ✅ Envoyer les documents par email aux acheteurs
  - ✅ Gérer les actualités, pages, etc.

###  **Utilisateurs simples** (ACHAT SANS COMPTE)
- **Qui** : Clients qui veulent acheter des documents
- **Compte** : ❌ **OPTIONNEL** - Peuvent acheter SANS créer de compte
- **Accès** : Frontend public uniquement
- **Fonctionnalités** :
  - ✅ Acheter un document sans s'inscrire
  - ✅ Remplir le formulaire de demande
  - ✅ Payer via Mobile Money (Orange Money, Moov Money)
  - ✅ Recevoir le document par email (une fois le paiement validé)

---

##  WORKFLOW POUR UN UTILISATEUR ANONYME

### Étape 1 : Sélection du document
```
GET /api/documents/documents/?actif=true
```
L'utilisateur voit la liste des documents disponibles avec prix et délai.

### Étape 2 : Création de la demande (SANS compte)
```

**Important** : La demande est créée **SANS utilisateur** (`utilisateur = null`), mais avec :
- ✅ Une référence unique
- ✅ L'email de réception
- ✅ Les données du formulaire

### Étape 3 : Ajout des pièces jointes (optionnel)
```

Une fois le paiement validé, la demande passe au statut `en_attente_traitement`.

### Étape 5 : Traitement par l'admin
L'admin peut :
- Assigner un notaire à la demande
- Préparer le document
- Envoyer le document par email

### Étape 6 : Envoi du document par email
```

Le document est envoyé à l'email fourni (`email_reception`) et le statut passe à `document_envoye_email`.

---

## 🔍 CONSULTATION DE LA DEMANDE (Utilisateur anonyme)

L'utilisateur anonyme peut consulter sa demande via :

### Option 1 : Par email
```
GET /api/demandes/demandes/?email=client@example.com
```

### Option 2 : Par référence
```
GET /api/demandes/demandes/?reference=DEM-20240115-1234
```

---

## 👨‍💼 POUR L'ADMINISTRATEUR

### Suivi des ventes
L'admin peut voir **TOUTES** les demandes et ventes :

```
GET /api/demandes/demandes/
Authorization: Bearer <admin_token>
```

Il peut :
- ✅ Voir toutes les demandes (avec ou sans compte utilisateur)
- ✅ Filtrer par statut : `?statut=en_attente_traitement`
- ✅ Voir les statistiques : `/api/ventes/stickers/` (si applicable)
- ✅ Exporter les données

### Statistiques disponibles
- Nombre total de ventes
- Montant total des transactions
- Demandes par statut
- Demandes par document
- Demandes par période

---

## 🔐 AVANTAGES DE CE SYSTÈME

### ✅ Pour l'utilisateur anonyme
- **Pas besoin de créer un compte** - achat rapide
- **Référence unique** - peut suivre sa demande
- **Email suffisant** - pour recevoir le document

### ✅ Pour l'admin
- **Suivi complet** - voit toutes les ventes
- **Pas de confusion** - distingue les utilisateurs authentifiés des anonymes
- **Flexibilité** - peut traiter toutes les demandes de la même manière

---


## 🎯 CAS D'USAGE RECOMMANDÉS

### Utilisateur anonyme devrait utiliser si :
- ✅ Achat ponctuel d'un document
- ✅ Ne prévoit pas de commander régulièrement
- ✅ Veut une transaction rapide

### Créer un compte devrait être recommandé si :
- ✅ L'utilisateur prévoit plusieurs commandes
- ✅ Il veut un historique complet de ses achats
- ✅ Il veut recevoir des notifications

---



## 📝 RÉSUMÉ FINAL

**Réponse à votre question :**

> "Est-ce que seul l'admin doit avoir un compte ?"

**NON !** Le système permet :
- ✅ **Admins** : Compte obligatoire pour gérer le back-office
- ✅ **Utilisateurs simples** : Peuvent acheter SANS compte
- ✅ **Admin peut envoyer le document** par email à l'acheteur après paiement
- ✅ **Admin peut suivre toutes les ventes** (avec ou sans compte utilisateur)

Le système est maintenant conforme à vos exigences ! 🎉

