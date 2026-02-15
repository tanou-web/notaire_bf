# Guide d'Hébergement sur Hostinger VPS

Ce guide explique comment déployer votre projet **notaire_bf** sur votre VPS Hostinger.

## 1. Connexion SSH au VPS
Récupérez l'adresse IP et le mot de passe root depuis votre [panel Hostinger](https://hpanel.hostinger.com/vps/1379290/overview).
```bash
ssh root@VOTRE_IP_VPS
```

## 2. Mise à jour et Installation des Dépendances
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv libpq-dev postgresql postgresql-contrib nginx curl -y
```

## 3. Configuration de la Base de Données (PostgreSQL)
Même si vous avez `sqlite3` localement, nous recommandons PostgreSQL pour la production (déjà présent dans vos `requirements.txt`).
```bash
sudo -u postgres psql
```
Dans l'interface psql :
```sql
CREATE DATABASE notaire_db;
CREATE USER notaire_user WITH PASSWORD 'votre_mot_de_passe_fort';
ALTER ROLE notaire_user SET client_encoding TO 'utf8';
ALTER ROLE notaire_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE notaire_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE notaire_db TO notaire_user;
\q
```

## 4. Préparation du Projet sur le VPS
Clonez votre code ou transférez-le (sans le dossier `.venv`).

```bash
mkdir -p /var/www/notaire_bf
cd /var/www/notaire_bf
# Transférez vos fichiers ici via SCP ou Git
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configuration de l'environnement
Créez un fichier `.env` à la racine du projet sur le serveur :
```bash
nano .env
```
Ajoutez vos variables de production (SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, ALLOWED_HOSTS).

## 6. Configuration de Gunicorn (Systemd)
Créez un service pour que Django tourne en arrière-plan.
```bash
sudo nano /etc/systemd/system/gunicorn.service
```
Contenu :
```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/notaire_bf
ExecStart=/var/www/notaire_bf/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock notaires_bf.wsgi:application

[Install]
WantedBy=multi-user.target
```
Démarrez le service :
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 7. Configuration de Nginx
```bash
sudo nano /etc/nginx/sites-available/notaire_bf
```
Contenu :
```nginx
server {
    listen 80;
    server_name burkinanotaires.com www.burkinanotaires.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    # Dossier pour la validation SSL (Certbot)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location /static/ {
        root /var/www/notaire_bf;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```
Activez la configuration :
```bash
sudo ln -sf /etc/nginx/sites-available/notaire_bf /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Finalisation (Migrations et Statiques)
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

## 9. HTTPS (Certbot)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d burkinanotaires.com -d www.burkinanotaires.com
```
