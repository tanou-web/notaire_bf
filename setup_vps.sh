#!/bin/bash

# Script d'automatisation pour le déploiement sur Hostinger VPS
# Domaine : burkinanotaires.com

set -e

PROJECT_NAME="notaire_bf"
PROJECT_DIR="/var/www/$PROJECT_NAME"
DOMAIN="burkinanotaires.com"

echo "--- Début de l'installation du serveur pour $DOMAIN ---"

# 1. Mise à jour du système
sudo apt update && sudo apt upgrade -y

# 2. Installation des paquets nécessaires
sudo apt install python3-pip python3-venv libpq-dev postgresql postgresql-contrib nginx curl certbot python3-certbot-nginx -y

# 3. Création du dossier projet
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

echo "--- Configuration de PostgreSQL ---"
# Note: L'utilisateur devra configurer sa DB manuellement ou nous pouvons automatiser une partie
# Mais pour la sécurité, mieux vaut le faire une fois connecté.

# 4. Préparation de Gunicorn Service
echo "--- Configuration de Gunicorn ---"
cat <<EOF | sudo tee /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock notaires_bf.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# 5. Configuration de Nginx
echo "--- Configuration de Nginx ---"
cat <<EOF | sudo tee /etc/nginx/sites-available/$PROJECT_NAME
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }

    # Dossier pour la validation SSL (Certbot)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location /static/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

echo "--- Installation terminée ! ---"
echo "Prochaines étapes :"
echo "1. Clonez le code dans $PROJECT_DIR"
echo "2. Créez le venv : python3 -m venv venv"
echo "3. Installez les requirements : pip install -r requirements.txt"
echo "4. Configurez votre fichier .env"
echo "5. Démarrez gunicorn : sudo systemctl enable --now gunicorn"
echo "6. Activez le SSL : sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
