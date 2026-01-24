# Guide : Upload de fichiers avec FormData dans les inscriptions d'événements

## 🎯 Problème identifié
Quand vous avez des champs de type `file` dans vos formulaires d'événement, le frontend doit envoyer les données en `multipart/form-data` au lieu de JSON simple.

## 📝 Format d'envoi correct

### ❌ Mauvais format (JSON seul)
```javascript
const data = {
  evenement: 8,
  nom: "Dupont",
  prenom: "Jean",
  email: "jean@example.com",
  telephone: "0123456789",
  reponses: [
    { champ: 1, valeur: "Texte" },
    { champ: 2, valeur: 30 },
    { champ: 3, valeur: fichier }  // ❌ Problème ici
  ]
};

fetch('/api/evenements/inscriptions/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

### ✅ Bon format (FormData avec fichiers)
```javascript
const formData = new FormData();

// Champs principaux
formData.append('evenement', '8');
formData.append('nom', 'Dupont');
formData.append('prenom', 'Jean');
formData.append('email', 'jean@example.com');
formData.append('telephone', '0123456789');

// Réponses (format spécial pour les arrays)
formData.append('reponses', JSON.stringify([
  { champ: 1, valeur: "Texte" },
  { champ: 2, valeur: 30 },
  { champ: 3, valeur: "nom_du_fichier.pdf" }  // Nom du fichier, pas l'objet File
]));

// Fichiers séparés
const fichierChamp3 = document.getElementById('champ_3').files[0];
if (fichierChamp3) {
  formData.append('fichier_champ_3', fichierChamp3);  // Clé spéciale pour le fichier
}

// Envoi
fetch('/api/evenements/inscriptions/', {
  method: 'POST',
  body: formData  // ❌ PAS de Content-Type, laissé automatique
});
```

## 🔧 Solution complète pour React/Vue

```javascript
const handleSubmit = async (formData) => {
  const formDataToSend = new FormData();

  // Champs de base
  formDataToSend.append('evenement', formData.evenement);
  formDataToSend.append('nom', formData.nom);
  formDataToSend.append('prenom', formData.prenom);
  formDataToSend.append('email', formData.email);
  formDataToSend.append('telephone', formData.telephone);

  // Construire les réponses
  const reponses = [];
  formData.champs.forEach((champ, index) => {
    let valeur = champ.valeur;

    if (champ.type === 'file' && champ.fichier) {
      // Pour les fichiers, on met juste le nom du fichier dans la valeur
      valeur = champ.fichier.name;
      // Et on ajoute le fichier séparément
      formDataToSend.append(`fichier_champ_${champ.id}`, champ.fichier);
    }

    reponses.push({
      champ: champ.id,
      valeur: valeur
    });
  });

  formDataToSend.append('reponses', JSON.stringify(reponses));

  try {
    const response = await fetch('/api/evenements/inscriptions/', {
      method: 'POST',
      body: formDataToSend
    });

    const result = await response.json();
    console.log('Succès:', result);
  } catch (error) {
    console.error('Erreur:', error);
  }
};
```

## 📋 Formats FormData acceptés

### Format 1 : `reponses[0].champ` (recommandé)
```
evenement=8
nom=Dupont
prenom=Jean
email=jean@example.com
telephone=0123456789
reponses=[{"champ":1,"valeur":"Texte"},{"champ":2,"valeur":30},{"champ":3,"valeur":"doc.pdf"}]
fichier_champ_3=@document.pdf
```

### Format 2 : `reponses.0.champ` (avec points)
```
evenement=8
nom=Dupont
reponses.0.champ=1
reponses.0.valeur=Texte
reponses.1.champ=2
reponses.1.valeur=30
fichier_champ_3=@document.pdf
```

## 🔍 Diagnostic

Pour vérifier que vos fichiers sont envoyés correctement :

1. **Dans le navigateur** (F12 → Network) :
   - Vérifiez que la requête est en `multipart/form-data`
   - Vérifiez que les fichiers apparaissent dans Form Data

2. **Logs du serveur** :
   ```python
   # Ajoutez temporairement dans views.py
   import logging
   logger = logging.getLogger(__name__)

   def create(self, request, *args, **kwargs):
       logger.info(f"FILES: {request.FILES}")
       logger.info(f"DATA: {request.data}")
       return super().create(request, *args, **kwargs)
   ```

## ⚠️ Points importants

1. **Ne pas définir `Content-Type`** : Laissez le navigateur le définir automatiquement
2. **Noms de fichiers dans `valeur`** : Pour les champs fichier, mettez le nom du fichier
3. **Fichiers séparés** : Envoyez les fichiers avec des clés comme `fichier_champ_{id}`
4. **Validation côté serveur** : Le serveur vérifie la taille (max 10MB) et l'extension

## 🎯 Test rapide

Pour tester sans frontend :
```bash
curl -X POST \
  -F "evenement=8" \
  -F "nom=Test" \
  -F "prenom=Curl" \
  -F "email=test@example.com" \
  -F "telephone=0123456789" \
  -F "reponses=[{\"champ\":1,\"valeur\":\"Test\"},{\"champ\":3,\"valeur\":\"test.pdf\"}]" \
  -F "fichier_champ_3=@/path/to/test.pdf" \
  http://localhost:8000/api/evenements/inscriptions/
```
