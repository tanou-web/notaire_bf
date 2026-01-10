# Configuration SMS Aqilas - Guide d'installation

## ⚠️ IMPORTANT : Envoi SMS obligatoire

Depuis la dernière mise à jour, **l'envoi de SMS est maintenant obligatoire** lors de la création d'un compte. Un code OTP est automatiquement généré et envoyé par SMS au numéro de téléphone fourni lors de l'inscription.

## Configuration requise

### 1. Obtenir vos identifiants Aqilas

1. Visitez le site web d'Aqilas : https://www.aqilas.com
2. Créez un compte ou connectez-vous à votre compte existant
3. Accédez à votre tableau de bord pour obtenir :
   - **API Key** (clé API)
   - **API Secret** (secret API)

### 2. Configurer le fichier .env

Le fichier `.env` a été créé à la racine du projet. Vous devez remplir les variables suivantes :

```env
# ⚠️ OBLIGATOIRES - Sans ces valeurs, l'envoi de SMS échouera
SMS_PROVIDER=aqilas
AQILAS_API_KEY=votre-cle-api-aqilas
AQILAS_API_SECRET=votre-secret-api-aqilas
AQILAS_SENDER_ID=NOTAIRES
AQILAS_API_URL=https://www.aqilas.com/api/v1
AQILAS_TIMEOUT=30
```

### 3. Variables à configurer

| Variable | Description | Obligatoire | Exemple |
|----------|-------------|-------------|---------|
| `SMS_PROVIDER` | Fournisseur SMS (doit être 'aqilas') | ✅ Oui | `aqilas` |
| `AQILAS_API_KEY` | Clé API Aqilas | ✅ Oui | `ak_1234567890abcdef` |
| `AQILAS_API_SECRET` | Secret API Aqilas | ✅ Oui | `sk_abcdef1234567890` |
| `AQILAS_SENDER_ID` | Nom de l'expéditeur (max 11 caractères) | ⚠️ Recommandé | `NOTAIRES` |
| `AQILAS_API_URL` | URL de l'API Aqilas | ⚠️ Optionnel | `https://www.aqilas.com/api/v1` |
| `AQILAS_TIMEOUT` | Timeout en secondes | ⚠️ Optionnel | `30` |

### 4. Vérifier la configuration

Après avoir configuré le fichier `.env`, redémarrez votre serveur Django :

```bash
python manage.py runserver
```

### 5. Tester l'envoi de SMS

Pour tester que la configuration fonctionne :

1. Créez un nouveau compte via l'API d'inscription
2. Vérifiez que vous recevez un SMS avec le code OTP
3. Vérifiez les logs dans `apps/communications/models.py` (table `CommunicationsSmslog`)

## Comportement en cas d'erreur

Si l'envoi de SMS échoue lors de la création d'un compte :

- ❌ **La création du compte sera annulée** (transaction atomique)
- ❌ **L'utilisateur ne sera pas créé en base de données**
- ❌ **Un message d'erreur sera retourné** à l'utilisateur

Cela garantit que seuls les utilisateurs ayant reçu leur code OTP peuvent créer un compte.

## Dépannage

### Erreur : "Impossible d'envoyer le SMS de vérification"

**Causes possibles :**
1. Variables d'environnement non configurées ou incorrectes
2. Identifiants Aqilas invalides ou expirés
3. Problème de connexion réseau
4. Crédits SMS insuffisants sur votre compte Aqilas

**Solutions :**
1. Vérifiez que toutes les variables sont correctement définies dans `.env`
2. Vérifiez vos identifiants Aqilas sur votre compte
3. Vérifiez votre connexion internet
4. Vérifiez votre solde de crédits SMS sur Aqilas

### Erreur : "Timeout de l'API Aqilas"

**Solution :**
- Augmentez la valeur de `AQILAS_TIMEOUT` dans le fichier `.env` (par exemple, `60`)

## Support

Pour plus d'informations sur l'API Aqilas :
- Documentation : https://www.aqilas.com/docs
- Support : contactez le support Aqilas

## Notes de sécurité

⚠️ **IMPORTANT :**
- Ne commitez JAMAIS le fichier `.env` dans Git
- Le fichier `.env` est déjà dans `.gitignore`
- Gardez vos identifiants API secrets et ne les partagez jamais
- Utilisez des identifiants différents pour le développement et la production
