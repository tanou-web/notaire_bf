# 🌊 Guide de Déploiement Complet sur DigitalOcean

Ce guide vous accompagne de A à Z pour héberger votre projet **Notaire BF** sur DigitalOcean.

---

## 🏗️ Architecture Choisie
Nous allons utiliser l'architecture "PaaS" (Platform as a Service) de DigitalOcean, appelée **App Platform**.
*   **Pourquoi ?** C'est l'équivalent de Render/Heroku. Pas de serveurs à gérer, pas de mises à jour de sécurité Linux à faire, déploiement automatique depuis GitHub.
*   **Alternative (Droplet)** : C'est moins cher mais demande des compétences Linux avancées (Nginx, Gunicorn, Systemd, Firewall). **Ce guide se concentre sur App Platform** pour la simplicité et la fiabilité.

---

## 1. 🌐 Nom de Domaine (.com)

Pour un `.com`, nous recommandons ces registrars pour leur prix (~10-12$/an) et sécurité :
1.  **Namecheap** (www.namecheap.com)
2.  **Porkbun** (www.porkbun.com)
3.  **Cloudflare** (www.cloudflare.com) - Prix coûtant, très rapide.

**Action :**
1.  Achetez votre domaine (ex: `notaires-bf.com`).
2.  Gardez l'accès au panneau de contrôle DNS, nous y reviendrons à la fin.

---

## 2. ☁️ Création du Projet sur DigitalOcean

1.  Créez un compte sur **[DigitalOcean](https://www.digitalocean.com)** (si n'est pas déjà fait).
2.  Dans le dashboard, créez un nouveau **Project** (ex: "Notaire BF").

---

## 3. 🗄️ Base de Données & Stockage (Avant le code)

Django a besoin d'une base de données et d'un endroit pour stocker les fichiers uploadés (images, PDF).

### A. Base de Données (PostgreSQL)
1.  Cliquez sur **Create > Database**.
2.  Choisissez **PostgreSQL**.
3.  Choisissez le plan :
    *   **Dev / Hobby** : ~15$/mois (Suffisant pour démarrer).
    *   *Note : App Platform propose aussi des "Dev Databases" moins chères (~7$) directement lors de la création de l'App.*
4.  Choisissez la région : **Frankfurt** ou **London** (Plus proche du Burkina).

### B. Stockage Fichiers (Spaces - S3 Compatible)
Pour que les images ne disparaissent pas à chaque redémarrage :
1.  Cliquez sur **Create > Spaces**.
2.  Choisissez une région (ex: Frankfurt).
3.  Nommez-le (ex: `notaires-bf-media`).
4.  Une fois créé, allez dans **Settings** du Space pour récupérer :
    *   **Origin Endpoint** (ex: `https://notaires-bf-media.fra1.digitaloceanspaces.com`).
5.  Allez dans le menu principal **API > Spaces Keys** et générez une clé :
    *   **Key ID**
    *   **Secret**
    *   *(Gardez-les précieusement !)*

---

## 4. 🚀 Déploiement de l'Application (App Platform)

1.  Allez dans **Apps** > **Create App**.
2.  **Service Provider** : Choisissez **GitHub**.
3.  Sélectionnez votre repository `notaire_bf`.
4.  **Source Directory** : `/` (racine).
5.  **Autodetect** : DigitalOcean va détecter Python/Django.
6.  **Resources** :
    *   Choisissez le plan **Basic** (~5-10$/mois).
    *   CPU: 512MB RAM | 1 vCPU est un bon début.

### Configuration des commandes
*   **Build Command** : DigitalOcean va proposer une commande par défaut. Assurez-vous qu'elle ressemble à :
    ```bash
    pip install -r requirements.txt && python manage.py collectstatic --noinput
    ```
*   **Run Command** :
    ```bash
    gunicorn notaires_bf.wsgi:application --bind 0.0.0.0:$PORT
    ```

### Variables d'Environnement (Environment Variables)
C'est l'étape CRITIQUE. Vous devez ajouter toutes ces clés dans l'interface de l'App (Section "Envs") :

| Clé | Valeur (Exemple) |
| :--- | :--- |
| `DEBUG` | `False` |
| `SECRET_KEY` | *(Générez une longue chaîne aléatoire)* |
| `ALLOWED_HOSTS` | `notaires-bf.com,votre-app.ondigitalocean.app` |
| `DATABASE_URL` | *(Lien automatique si vous attachez la DB, sinon `postgresql://user:pass@host:port/db`)* |
| `AWS_ACCESS_KEY_ID` | *(Votre Key ID Spaces)* |
| `AWS_SECRET_ACCESS_KEY` | *(Votre Secret Spaces)* |
| `AWS_STORAGE_BUCKET_NAME` | `notaires-bf-media` (Nom du Space) |
| `AWS_S3_REGION_NAME` | `fra1` (Code de la région) |
| `AWS_S3_ENDPOINT_URL` | `https://fra1.digitaloceanspaces.com` (Sans le nom du bucket !) |
| `AWS_S3_CUSTOM_DOMAIN` | `notaires-bf-media.fra1.digitaloceanspaces.com` |
| `EMAIL_HOST` | `smtp.sendgrid.net` |
| `EMAIL_PORT` | `587` |
| `EMAIL_HOST_USER` | `apikey` |
| `EMAIL_HOST_PASSWORD` | *(Votre Clé API SendGrid)* |

---

## 5. 🔗 Lier le Nom de Domaine

1.  Une fois l'application déployée ("Health Checks passed").
2.  Allez dans l'onglet **Settings** de votre App.
3.  Section **Domains** > **Add Domain**.
4.  Entrez `notaires-bf.com`.
5.  DigitalOcean vous donnera des **Serveurs DNS (Nameservers)** (ex: `ns1.digitalocean.com`, `ns2...`, `ns3...`).
6.  Allez chez votre registrar (Namecheap/Porkbun) et remplacez leurs DNS par ceux de DigitalOcean.
7.  Attendez quelques heures : HTTPS sera activé automatiquement !

---

## 💰 Estimation Coût Mensuel "Réaliste"

1.  **Nom de Domaine** : ~1$ / mois (payé à l'année ~12$).
2.  **App Platform (Backend)** : 5$ - 12$.
3.  **Database (PostgreSQL)** : 15$ (Managed) ou 7$ (Dev).
4.  **Spaces (Stockage)** : 5$ (250GB inclus).
5.  **Email (SendGrid)** : Gratuit (ou plan à 20$).

**Total Estimé : ~30$ / mois** pour une infrastructure professionnelle, redondante et sauvegardée.

---

## ❓ FAQ

**Q: Puis-je utiliser un Droplet à 6$ pour tout faire ?**
R: Oui, mais vous devrez :
*   Installer Linux, Python, PostgreSQL, Nginx, Gunicorn.
*   Configurer le Firewall (UFW).
*   Gérer les backups MySQL vous-même.
*   Gérer les certificats SSL (Certbot) vous-même.
*   Surveiller les logs et les pannes.
*   *Notre conseil : Le temps que vous perdez à gérer le serveur vaut plus que l'économie réalisée.*

**Q: Et pour les emails ?**
R: Suivez le guide `DIGITALOCEAN_SENDGRID_SETUP.md` déjà présent dans vos fichiers pour configurer SendGrid (via le Marketplace DO ou directement).
