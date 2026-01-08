# 🏛️ Notaire BF - Système de Gestion Notariale

[![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Burkina Faso](https://img.shields.io/badge/Pays-Burkina%20Faso-yellow.svg)](https://burkinafaso.bf/)

Système complet de gestion numérique pour l'Ordre des Notaires du Burkina Faso**

## 📋 Vue d'ensemble

**Notaire BF** est une plateforme digitale complète conçue spécifiquement pour moderniser et digitaliser les services notariaux au Burkina Faso. Le système offre une solution intégrée pour la gestion des actes notariés, des demandes clients, des paiements sécurisés et de l'administration de l'Ordre des Notaires.

### ✨ Fonctionnalités principales

#### 🏢 **Gestion de l'Organisation**
- 👥 Gestion des membres du bureau et organes dirigeants
- 📊 Historique et missions de l'Ordre
- 🎯 Gestion des commissions et comités
- 📈 Tableaux de bord et statistiques

#### 👤 **Gestion des Utilisateurs**
- 🔐 Authentification JWT sécurisée
- 👥 Profils utilisateurs (Notaires, Clients, Administrateurs)
- 📧 Vérification email et téléphone
- 🎫 Gestion des rôles et permissions

#### 📄 **Gestion Documentaire**
- 📑 Création et gestion d'actes notariés
- 🔍 Recherche et archivage intelligent
- 📎 Gestion des pièces jointes
- 🔒 Signature électronique (en développement)

#### 💳 **Paiements Intégrés**
- 🟠 **Orange Money** Burkina Faso
- 📱 **Moov Money** Burkina Faso
- 💰 Suivi des transactions en temps réel
- 📊 Rapports financiers détaillés

#### 🌐 **Services Publics**
- 📝 Soumission de demandes en ligne
- 💡 Conseils juridiques et guides
- 📰 Actualités et publications
- 📞 Support et contact

#### 🔍 **Système d'Audit**
- 📊 Logs détaillés de toutes les actions
- 🚨 Détection des fraudes et anomalies
- 📈 Métriques de performance
- 🛡️ Monitoring de sécurité

## 🏗️ Architecture Technique

### Technologies utilisées
- **Backend**: Django 5.2.5 + Django REST Framework
- **Base de données**: PostgreSQL (production) / SQLite (développement)
- **Authentification**: JWT (JSON Web Tokens)
- **Stockage**: AWS S3 pour les fichiers
- **Paiements**: APIs Orange Money & Moov Money
- **Documentation**: Swagger/OpenAPI
- **Tests**: Django Test Framework

### Structure modulaire
```
notaire_bf/
├── apps/
│   ├── utilisateurs/     # Gestion des comptes
│   ├── notaires/         # Profils notaires
│   ├── demandes/         # Demandes clients
│   ├── documents/        # Gestion documentaire
│   ├── paiements/        # Intégration paiements
│   ├── organisation/     # Gestion de l'Ordre
│   ├── audit/           # Système d'audit
│   ├── system/          # Configuration système
│   └── core/            # Pages CMS et configuration
├── notaires_bf/         # Configuration Django
└── requirements.txt     # Dépendances Python
```

## 🚀 Installation & Déploiement

### Prérequis
- Python 3.11+
- PostgreSQL 13+
- Git

### Installation rapide

```bash
# Cloner le repository
git clone <repository-url>
cd notaire_bf

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configuration des variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Migrations de base de données
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### Variables d'environnement

```bash
# Base de données
DB_NAME=notaire_bf
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Sécurité
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Authentification
JWT_SECRET_KEY=your-jwt-secret

# Services externes
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket

# Paiements
ORANGE_MONEY_API_KEY=your-orange-key
MOOV_MONEY_API_KEY=your-moov-key

# Email (SendGrid recommandé pour DigitalOcean)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=votre-cle-api-sendgrid
DEFAULT_FROM_EMAIL=noreply@votre-domaine.com
CONTACT_EMAIL=contact@votre-domaine.com

# Alternative cPanel (pour autres hébergeurs)
# EMAIL_HOST=mail.votre-domaine.com
# EMAIL_PORT=465
# EMAIL_USE_SSL=True
# EMAIL_USE_TLS=False
# EMAIL_HOST_USER=noreply@votre-domaine.com
# EMAIL_HOST_PASSWORD=votre-mot-de-passe-cpanel

# Ancienne configuration Gmail (alternative)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_USE_SSL=False
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

## 📖 API Documentation

### Endpoints principaux

#### Authentification
```
POST /api/auth/login/              # Connexion
POST /api/auth/logout/             # Déconnexion
POST /api/auth/password-reset/     # Réinitialisation mot de passe
```

#### Gestion des demandes
```
GET  /api/demandes/demandes/       # Lister les demandes
POST /api/demandes/demandes/       # Créer une demande
GET  /api/demandes/demandes/{id}/  # Détail d'une demande
```

#### Gestion documentaire
```
GET  /api/documents/documents/     # Lister les documents
POST /api/documents/documents/     # Téléverser un document
GET  /api/documents/textes-legaux/ # Textes juridiques
```

#### Paiements
```
GET  /api/paiements/transactions/  # Historique paiements
POST /api/paiements/transactions/  # Initier un paiement
```

#### Organisation
```
GET  /api/organisation/bureau/     # Membres du bureau
GET  /api/organisation/missions/   # Missions de l'Ordre
GET  /api/organisation/stats/      # Statistiques
```

## 🔒 Sécurité

### Fonctionnalités de sécurité
- ✅ Authentification JWT avec expiration
- ✅ Chiffrement des mots de passe (bcrypt)
- ✅ Protection CSRF
- ✅ Sanitisation des entrées
- ✅ Logs d'audit complets
- ✅ Rate limiting sur l'API
- ✅ Validation des permissions
- ✅ Chiffrement des données sensibles

### Conformité
- 📋 Respect des standards Django
- 🔐 Bonnes pratiques de sécurité web
- 📊 Audit trail complet
- 🛡️ Protection contre les vulnérabilités communes

## 📊 Métriques & Performance

### Couverture de tests
- **54 tests** actuellement
- **Couverture cible**: 80%+

### Performance
- ⚡ Temps de réponse API: <500ms
- 📈 Gestion de 1000+ utilisateurs simultanés
- 💾 Optimisation des requêtes SQL
- 🗄️ Cache Redis (recommandé)

## 🤝 Contribution

### Processus de développement
1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit vos changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

### Standards de code
- 🔧 **Black** pour le formatage
- 🐛 **Flake8** pour le linting
- 📝 **Docstrings** pour toute fonction publique
- ✅ **Tests** pour toute nouvelle fonctionnalité

## 📞 Support & Contact

- 📧 **Email**: contact@notaires.bf
- 🌐 **Site web**: https://notaires.bf
- 📱 **Téléphone**: +226 XX XX XX XX
- 🏢 **Adresse**: Ouagadougou, Burkina Faso

## 📜 Licence

**Propriétaire** - Tous droits réservés
Ordre des Notaires du Burkina Faso

## 🙏 Remerciements

- **Django Community** pour le framework exceptionnel
- **Burkina Faso** pour le soutien au développement numérique
- **Ordre des Notaires BF** pour la confiance accordée

---

**Développé avec ❤️ au Burkina Faso** 🇧🇫

*Dernière mise à jour: Janvier 2025*
