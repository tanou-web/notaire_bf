# 🚀 Guide d'Installation - Notaire BF

## Prérequis système

### Matériel recommandé
- **RAM**: 4GB minimum, 8GB recommandé
- **CPU**: 2 cœurs minimum
- **Stockage**: 10GB disponible
- **Réseau**: Connexion internet stable

### Logiciels requis
- **Python**: 3.11 ou supérieur
- **Base de données**: PostgreSQL 13+ (production) ou SQLite (développement)
- **Serveur web**: Nginx (recommandé) ou Apache
- **Cache**: Redis (optionnel mais recommandé)

## Installation étape par étape

### 1. Préparation de l'environnement

```bash
# Créer le répertoire du projet
mkdir notaire-bf
cd notaire-bf

# Cloner le repository
git clone <repository-url> .
```

### 2. Configuration Python

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Mettre à jour pip
pip install --upgrade pip
```

### 3. Installation des dépendances

```bash
# Installer les packages Python
pip install -r requirements.txt

# Vérifier l'installation
python --version
pip list | grep -E "(Django|djangorestframework)"
```

### 4. Configuration de la base de données

#### Option A: PostgreSQL (Production)
```bash
# Installer PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Créer la base de données
sudo -u postgres psql
CREATE DATABASE notaire_bf;
CREATE USER notaire_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE notaire_bf TO notaire_user;
\q
```

#### Option B: SQLite (Développement)
```bash
# SQLite est configuré par défaut
# Aucune configuration supplémentaire requise
```

### 5. Configuration des variables d'environnement

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer le fichier .env
nano .env  # ou votre éditeur préféré
```

Contenu du fichier `.env` :
```bash
# Configuration Django
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Base de données
DB_ENGINE=django.db.backends.postgresql
DB_NAME=notaire_bf
DB_USER=notaire_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Authentification
JWT_SECRET_KEY=your-jwt-secret-key

# Services de paiement
ORANGE_MONEY_API_KEY=your_orange_api_key
ORANGE_MONEY_API_SECRET=your_orange_api_secret
ORANGE_MONEY_MERCHANT_CODE=your_merchant_code

MOOV_MONEY_API_KEY=your_moov_api_key
MOOV_MONEY_API_SECRET=your_moov_api_secret
MOOV_MONEY_MERCHANT_ID=your_merchant_id

# Stockage AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=notaire-bf-documents
AWS_S3_REGION_NAME=eu-west-1

# Configuration email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=contact@notaires.bf
EMAIL_HOST_PASSWORD=your_app_password

# Sécurité
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# URL de base
BASE_URL=https://notaires.bf
```

### 6. Initialisation de la base de données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# (Optionnel) Charger des données d'exemple
python manage.py loaddata fixtures/initial_data.json
```

### 7. Configuration du serveur web

#### Avec Nginx + Gunicorn (Production)

**Installer Gunicorn**:
```bash
pip install gunicorn
```

**Créer le fichier systemd pour Gunicorn**:
```bash
sudo nano /etc/systemd/system/notaire-bf.service
```

Contenu du service :
```ini
[Unit]
Description=Notaire BF Django Application
After=network.target

[Service]
User=notaire
Group=notaire
WorkingDirectory=/home/notaire/notaire-bf
Environment="PATH=/home/notaire/notaire-bf/venv/bin"
ExecStart=/home/notaire/notaire-bf/venv/bin/gunicorn --workers 3 --bind unix:/home/notaire/notaire-bf.sock notaires_bf.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**Configuration Nginx**:
```bash
sudo nano /etc/nginx/sites-available/notaire-bf
```

Contenu Nginx :
```nginx
server {
    listen 80;
    server_name notaires.bf www.notaires.bf;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/notaire/notaire-bf/static/;
    }

    location /media/ {
        alias /home/notaire/notaire-bf/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/notaire/notaire-bf.sock;
    }
}

server {
    listen 443 ssl http2;
    server_name notaires.bf www.notaires.bf;

    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;

    # SSL configuration...
    # (Configuration SSL complète recommandée)

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/notaire/notaire-bf.sock;
    }
}
```

### 8. Configuration HTTPS (Let's Encrypt)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir le certificat SSL
sudo certbot --nginx -d notaires.bf -d www.notaires.bf
```

### 9. Tests et vérifications

```bash
# Exécuter les tests
python manage.py test

# Vérifier les URLs
python manage.py check --deploy

# Tester le serveur en développement
python manage.py runserver 0.0.0.0:8000
```

### 10. Monitoring et maintenance

#### Configuration des logs
```bash
# Créer les répertoires de logs
sudo mkdir -p /var/log/notaire-bf
sudo chown notaire:notaire /var/log/notaire-bf

# Configurer la rotation des logs
sudo nano /etc/logrotate.d/notaire-bf
```

#### Sauvegarde automatique
```bash
# Script de sauvegarde
sudo nano /usr/local/bin/backup-notaire-bf.sh
```

Contenu du script de sauvegarde :
```bash
#!/bin/bash
BACKUP_DIR="/home/notaire/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Sauvegarde base de données
pg_dump notaire_bf > $BACKUP_DIR/db_$DATE.sql

# Sauvegarde fichiers médias
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/notaire/notaire-bf/media/

# Nettoyage des anciennes sauvegardes (garde 30 jours)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## Dépannage

### Problèmes courants

#### Erreur de connexion à la base de données
```bash
# Vérifier que PostgreSQL fonctionne
sudo systemctl status postgresql

# Vérifier les credentials
psql -h localhost -U notaire_user -d notaire_bf
```

#### Erreur de permissions sur les fichiers statiques
```bash
# Corriger les permissions
sudo chown -R notaire:notaire /home/notaire/notaire-bf/
sudo chmod -R 755 /home/notaire/notaire-bf/
```

#### Problème avec les variables d'environnement
```bash
# Vérifier que .env est chargé
python -c "import os; print(os.getenv('DEBUG'))"
```

## Support

Pour toute question ou problème :
- 📧 Email: support@notaires.bf
- 📱 Téléphone: +226 XX XX XX XX
- 📖 Documentation: https://docs.notaires.bf

---

**Installation terminée ?** Passez à la [Configuration avancée](CONFIGURATION.md) !

