# 📱 Composants React pour l'API Événements

## 🎯 Vue d'ensemble

Ces composants React permettent de gérer les inscriptions aux événements avec support complet des formulaires dynamiques et uploads de fichiers.

## 📁 Fichiers

- `ReactFileUploadComponent.jsx` - Composant spécialisé pour l'upload de fichiers
- `ReactInscriptionForm.jsx` - Formulaire complet d'inscription
- `InscriptionForm.css` - Styles pour les composants

## 🚀 Installation et utilisation

### 1. Importer les composants

```jsx
import InscriptionForm from './ReactInscriptionForm';
import './InscriptionForm.css'; // Importer les styles
```

### 2. Utiliser le formulaire d'inscription

```jsx
function App() {
  return (
    <div className="app">
      <InscriptionForm evenementId={8} />
    </div>
  );
}
```

## 🔧 Personnalisation

### Props du composant InscriptionForm

```jsx
<InscriptionForm
  evenementId={8}  // ID de l'événement (requis)
/>
```

### Styles personnalisés

Le CSS utilise des classes BEM. Vous pouvez personnaliser :

```css
/* Couleurs principales */
.inscription-form {
  --primary-color: #007bff;
  --success-color: #28a745;
  --error-color: #dc3545;
  --border-color: #ddd;
}

/* Espacement */
.field-group {
  --field-spacing: 20px;
}

/* Bordures et ombres */
.inscription-form {
  --border-radius: 8px;
  --box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
```

## 🔍 Fonctionnement détaillé

### 1. Chargement du formulaire

Au montage, le composant :
1. Appelle `GET /api/evenements/{id}/formulaire/`
2. Trie les champs par ordre
3. Initialise l'état des champs dynamiques

### 2. Gestion des fichiers

Pour chaque champ de type `file` :
- Input caché pour la sélection
- Bouton stylisé pour déclencher la sélection
- Aperçu du fichier sélectionné
- Bouton de suppression
- Validation côté client

### 3. Validation

**Côté client :**
- Champs obligatoires
- Formats d'email
- Types de fichiers et tailles
- Extensions autorisées

**Côté serveur :**
- Même validation + contraintes supplémentaires
- Stockage des fichiers

### 4. Soumission

1. **Validation complète** du formulaire
2. **Construction du FormData** :
   ```javascript
   const formData = new FormData();
   formData.append('evenement', id);
   formData.append('nom', valeur);
   // ... autres champs

   // Réponses JSONifiées
   formData.append('reponses', JSON.stringify(reponses));

   // Fichiers séparés
   formData.append('fichier_champ_6', fichierObjet);
   ```
3. **Envoi sans Content-Type** (automatique)
4. **Gestion des erreurs** spécifiques

## 📊 États du composant

| État | Description | Affichage |
|------|-------------|-----------|
| `chargement` | Chargement du formulaire | Spinner + message |
| `soumission` | Envoi en cours | Bouton disabled + loader |
| `erreur` | Erreur de validation/soumission | Message d'erreur |
| `succes` | Inscription réussie | Message de confirmation |

## 🎨 Personnalisation avancée

### Ajouter un champ personnalisé

```jsx
// Dans le render du formulaire
{formulaire.map(champ => {
  if (champ.type === 'custom') {
    return <MonChampPersonnalise key={champ.id} champ={champ} />;
  }

  // ... autres types
})}
```

### Modifier la validation

```jsx
const validateForm = () => {
  const errors = {};

  // Validation personnalisée
  if (formData.email.includes('spam')) {
    errors.email = 'Adresse email suspecte';
  }

  // Validation par défaut
  return { ...errors, ...defaultValidation() };
};
```

### Upload avec progression

```jsx
const [uploadProgress, setUploadProgress] = useState(0);

// Dans handleSubmit
const xhr = new XMLHttpRequest();

xhr.upload.onprogress = (e) => {
  if (e.lengthComputable) {
    setUploadProgress(Math.round((e.loaded / e.total) * 100));
  }
};

// Utiliser xhr au lieu de fetch
```

## 🔧 Dépannage

### Erreur "415 Unsupported Media Type"
**Cause :** Content-Type défini manuellement
**Solution :** Retirer le header Content-Type

### Erreur "Fichier trop volumineux"
**Cause :** Fichier > 10MB
**Solution :** Compresser ou informer l'utilisateur

### Erreur "Extension non autorisée"
**Cause :** Format non supporté
**Solution :** Vérifier la liste des extensions acceptées

### Erreur "Champ obligatoire manquant"
**Cause :** Validation côté client défaillante
**Solution :** Vérifier la logique de validation

## 📋 Checklist d'intégration

- [ ] Importer les composants et styles
- [ ] Fournir l'`evenementId` correct
- [ ] Tester avec différents types de champs
- [ ] Tester l'upload de fichiers
- [ ] Vérifier la validation des erreurs
- [ ] Tester sur mobile (responsive)
- [ ] Personnaliser les styles si nécessaire

## 🎯 Points critiques

1. **FormData obligatoire** pour les fichiers
2. **Pas de Content-Type** dans les headers
3. **Clés `fichier_champ_{id}`** pour les fichiers
4. **Validation côté client** avant envoi
5. **Gestion d'état** pour UX fluide

---

*Ces composants sont prêts à être intégrés dans votre application React !* 🚀
