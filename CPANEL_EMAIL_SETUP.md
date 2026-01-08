# 🛠️ Configuration Email cPanel - Guide Notaire BF

## 📋 Vue d'ensemble

Ce guide explique comment configurer les emails avec cPanel pour votre système Notaire BF au lieu d'utiliser Gmail SMTP.

## ✅ Avantages de cPanel

- **Emails professionnels** : Utilisez votre propre domaine (@notaires.bf)
- **Meilleur taux de livraison** : Évite les filtres anti-spam
- **Gestion centralisée** : Tous les emails dans un seul panneau
- **Anti-spam intégré** : cPanel inclut des outils anti-spam
- **Sauvegarde automatique** : Vos emails sont sauvegardés

## 🔧 Configuration cPanel

### 1. Créer des comptes email

Dans votre cPanel, allez dans **"Email Accounts"** et créez :

```
noreply@notaires.bf    - Pour les emails système (vérifications, notifications)
contact@notaires.bf    - Pour les emails de contact
info@notaires.bf       - Pour les communications générales
```

### 2. Configuration DNS (Important !)

Assurez-vous que vos enregistrements MX pointent vers votre hébergement :

```
Type: MX
Name: @
Value: mail.notaires.bf
Priority: 0
```

### 3. Configuration Django

Les paramètres sont déjà configurés dans `settings/base.py`. Copiez votre fichier `.env` :

```bash
cp env.example .env
```

Puis éditez `.env` avec vos vraies valeurs :

```bash
# Configuration Email cPanel
EMAIL_HOST=mail.notaires.bf
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_USE_TLS=False
EMAIL_HOST_USER=noreply@notaires.bf
EMAIL_HOST_PASSWORD=votre_mot_de_passe_cpanel
DEFAULT_FROM_EMAIL=noreply@notaires.bf
CONTACT_EMAIL=contact@notaires.bf
```

### 4. Configuration des ports cPanel

**Port recommandé : 465 (SSL)**

Certains hébergeurs utilisent :
- Port 465 (SSL) - recommandé
- Port 587 (TLS) - alternatif
- Port 25 (non chiffré) - éviter en production

## 🧪 Test de la configuration

### Test basique avec Django

```python
# Dans votre shell Django
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test cPanel',
    'Ceci est un test d\'envoi email via cPanel',
    'noreply@notaires.bf',
    ['votre-email@test.com'],
    fail_silently=False,
)
```

### Test des fonctionnalités

1. **Inscription utilisateur** : Vérifiez que l'email de vérification arrive
2. **Contact** : Testez le formulaire de contact
3. **Notifications** : Vérifiez les emails automatiques

## 🛡️ Sécurité cPanel

### Bonnes pratiques

1. **Mots de passe forts** : Utilisez des générateurs de mots de passe
2. **Authentification deux facteurs** : Activez 2FA sur cPanel
3. **Limites d'envoi** : Configurez des limites pour éviter le spam
4. **Monitoring** : Surveillez l'utilisation email

### Configuration anti-spam

Dans cPanel :
- Activez **SpamAssassin**
- Configurez **Apache SpamAssassin™**
- Ajoutez des filtres personnalisés si nécessaire

## 🔄 Migration depuis Gmail

### Étapes de migration

1. **Créer les comptes email** dans cPanel
2. **Tester** la nouvelle configuration
3. **Changer** les variables d'environnement
4. **Redémarrer** votre application
5. **Vérifier** que tous les emails fonctionnent
6. **Mettre à jour** la documentation si nécessaire

### Rollback possible

Si vous rencontrez des problèmes, vous pouvez toujours revenir à Gmail :

```bash
# Dans .env, commentez cPanel et décommentez Gmail
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_USE_SSL=False
```

## 📊 Monitoring et maintenance

### Métriques à surveiller

- **Taux de livraison** : Pourcentage d'emails délivrés
- **Plaintes spam** : Surveillez les rapports de spam
- **Temps de réponse** : Délais de livraison des emails
- **Erreurs SMTP** : Logs d'erreurs d'envoi

### Outils cPanel utiles

- **Email Deliverability** : Testez la réputation de votre domaine
- **Track Delivery** : Suivez l'état de livraison des emails
- **Email Filters** : Gérez les filtres anti-spam
- **Forwarders** : Redirigez les emails vers d'autres adresses

## 🚨 Dépannage

### Problèmes courants

#### "Authentication failed"
- Vérifiez le mot de passe du compte email
- Assurez-vous que le compte email existe dans cPanel

#### "Connection refused"
- Vérifiez le port (465 pour SSL)
- Confirmez que votre domaine pointe vers le bon serveur

#### "Emails arrivent en spam"
- Configurez correctement vos enregistrements SPF/DKIM
- Échauffez votre domaine email progressivement

#### "Taux de livraison faible"
- Évitez d'envoyer trop d'emails d'un coup
- Utilisez des adresses "From" cohérentes

## 📞 Support

Pour toute question concernant la configuration cPanel :
- Consultez la documentation de votre hébergeur
- Contactez le support cPanel de votre hébergeur
- Vérifiez les logs Django pour les erreurs détaillées

---

**✅ Configuration terminée ?** Testez et validez que tous les emails fonctionnent correctement avant la mise en production.
