# 🚀 **GUIDE COMPLET API ÉVÉNEMENTS - Frontend Developer**

## 📋 **Vue d'ensemble**

L'API des événements permet de :
- Gérer les événements et leurs formulaires dynamiques
- Soumettre des inscriptions avec validation automatique des types
- Gérer les fichiers uploadés

---

## 🎯 **APIs Disponibles**

### **1. Événements**

#### **GET** `/api/evenements/`
Liste tous les événements actifs

**Réponse :**
```json
[
  {
    "id": 8,
    "titre": "Test Formulaire Généré",
    "description": "Formation en ligne",
    "statut": "ouvert",
    "actif": true,
    "nombre_places": 100,
    "created_at": "2025-01-25T10:30:00Z"
  }
]
```

#### **GET** `/api/evenements/{id}/`
Détail d'un événement

#### **GET** `/api/evenements/{id}/formulaire/`
Champs du formulaire d'inscription

**Réponse :**
```json
{
  "evenement": 8,
  "formulaire": [
    {
      "id": 8,
      "label": "Nom complet",
      "type": "text",
      "obligatoire": true,
      "options": null
    },
    {
      "id": 9,
      "label": "âge",
      "type": "number",
      "obligatoire": false,
      "options": null
    }
  ]
}
```

#### **GET** `/api/evenements/choices/`
Liste des événements pour dropdown

**Réponse :**
```json
[
  [8, "Test Formulaire Généré"],
  [3, "bonjour"]
]
```

### **2. Inscriptions**

#### **POST** `/api/evenements/inscriptions/`
Créer une inscription

---

## 📝 **Types de Champs Supportés**

| Type | Description | Format Valeur | Exemple Frontend | Validation |
|------|-------------|---------------|------------------|------------|
| `text` | Champ texte simple | `string` | `"John Doe"` | Longueur max 255 |
| `textarea` | Zone de texte long | `string` | `"Description longue..."` | Illimité |
| `number` | Nombre entier/décimal | `string` → converti auto | `"32"` ou `"25.5"` | Chiffres uniquement |
| `date` | Date | `string` | `"14/11/2016"` ou `"2016-11-14"` | JJ/MM/AAAA ou AAAA-MM-JJ |
| `checkbox` | Case à cocher | `boolean` | `true` ou `false` | true/false uniquement |
| `select` | Liste déroulante | `string` | `"Avocat"` | Doit être dans options |
| `file` | Fichier upload | `string` (nom) | `"cv.pdf"` | Extensions limitées |

---

## 🔧 **Format des Données d'Inscription**

### **Structure Générale**
```javascript
const formData = new FormData();

// Champs de base
formData.append('evenement', '8');           // ID de l'événement
formData.append('nom', 'Doe');               // String
formData.append('prenom', 'John');           // String
formData.append('email', 'john@example.com'); // Email valide
formData.append('telephone', '+22612345678'); // String

// Réponses aux champs (JSON stringifié)
const reponses = [
  {"champ": 8, "valeur": "John Doe"},        // text
  {"champ": 9, "valeur": "32"},              // number (string accepté)
  {"champ": 10, "valeur": "Avocat"},         // select
  {"champ": 12, "valeur": "14/11/2016"},     // date
  {"champ": 13, "valeur": true}              // checkbox
];

formData.append('reponses', JSON.stringify(reponses));

// Fichiers (clés dynamiques)
formData.append('fichier_champ_39', fichierPDF); // File object
```

### **Exemple Complet Frontend (React/Vue/Angular)**

```javascript
// Récupération du formulaire
const getFormulaire = async (eventId) => {
  const response = await fetch(`/api/evenements/${eventId}/formulaire/`);
  const data = await response.json();
  return data.formulaire; // Array des champs
};

// Soumission de l'inscription
const submitInscription = async (eventId, formData, fichiers) => {
  const form = new FormData();

  // Champs de base
  form.append('evenement', eventId);
  form.append('nom', formData.nom);
  form.append('prenom', formData.prenom);
  form.append('email', formData.email);
  form.append('telephone', formData.telephone);

  // Construction des réponses
  const reponses = Object.entries(formData.champs).map(([champId, valeur]) => ({
    champ: parseInt(champId),
    valeur: valeur
  }));

  form.append('reponses', JSON.stringify(reponses));

  // Ajout des fichiers
  Object.entries(fichiers).forEach(([champId, fichier]) => {
    if (fichier) {
      form.append(`fichier_champ_${champId}`, fichier);
    }
  });

  const response = await fetch('/api/evenements/inscriptions/', {
    method: 'POST',
    body: form
  });

  return await response.json();
};
```

---

## 📋 **Gestion des Champs par Type**

### **Text (`text`)**
```javascript
// Input HTML standard
<input
  type="text"
  value={valeur}
  onChange={(e) => setValeur(e.target.value)}
  maxLength={255}
/>
```

### **Textarea (`textarea`)**
```javascript
<textarea
  value={valeur}
  onChange={(e) => setValeur(e.target.value)}
  rows={4}
/>
```

### **Number (`number`)**
```javascript
// Input number ou text (les deux fonctionnent)
<input
  type="number"
  value={valeur}
  onChange={(e) => setValeur(e.target.value)}
  min="0"
/>

// OU text (converti automatiquement)
<input
  type="text"
  value={valeur}
  onChange={(e) => setValeur(e.target.value)}
  pattern="[0-9]*[.,]?[0-9]*"
/>
```

### **Date (`date`)**
```javascript
// Input date HTML5
<input
  type="date"
  value={valeur} // Format AAAA-MM-JJ
  onChange={(e) => setValeur(e.target.value)}
/>

// OU text avec placeholder
<input
  type="text"
  value={valeur}
  onChange={(e) => setValeur(e.target.value)}
  placeholder="JJ/MM/AAAA"
/>
```

### **Checkbox (`checkbox`)**
```javascript
<input
  type="checkbox"
  checked={valeur}
  onChange={(e) => setValeur(e.target.checked)}
/>
```

### **Select (`select`)**
```javascript
<select
  value={valeur}
  onChange={(e) => setValeur(e.target.value)}
>
  <option value="">Choisir...</option>
  {champ.options.map(option => (
    <option key={option} value={option}>{option}</option>
  ))}
</select>
```

### **File (`file`)**
```javascript
<input
  type="file"
  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
  onChange={(e) => {
    const file = e.target.files[0];
    if (file && file.size > 10 * 1024 * 1024) { // 10MB max
      alert('Fichier trop volumineux (max 10MB)');
      return;
    }
    setFichier(file);
  }}
/>
```

---

## ✅ **Réponses API**

### **Succès (201 Created)**
```json
{
  "id": 123,
  "evenement": 8,
  "nom": "Doe",
  "prenom": "John",
  "email": "john@example.com",
  "telephone": "+22612345678",
  "statut": "en_attente",
  "created_at": "2025-01-25T12:00:00Z",
  "reponses": [
    {
      "champ": "Nom complet",
      "type": "text",
      "valeur": "John Doe"
    },
    {
      "champ": "âge",
      "type": "number",
      "valeur": 32
    }
  ]
}
```

### **Erreurs (400 Bad Request)**
```json
{
  "non_field_errors": ["Âge doit être un nombre"],
  "email": ["Email invalide"],
  "reponses": ["Champ 10 est obligatoire"]
}
```

---

## 🔒 **Règles de Validation**

### **Champs Obligatoires**
- Marqués `obligatoire: true` dans le formulaire
- Valeurs vides `null`, `""`, `[]` rejetées

### **Types de Validation par Champ**
- **Email** : Format email valide requis
- **Number** : Chiffres uniquement (converti automatiquement)
- **Date** : Formats JJ/MM/AAAA ou AAAA-MM-JJ
- **Select** : Valeur doit être dans `options`
- **File** : Extensions `.pdf,.jpg,.jpeg,.png,.doc,.docx` (max 10MB)

### **Places Disponibles**
- Vérification automatique des places restantes
- Statut passe à `complet` quand `nombre_places = 0`

---

## 📁 **Structure du Projet Frontend**

### **Types TypeScript (optionnel)**
```typescript
interface Champ {
  id: number;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'date' | 'checkbox' | 'select' | 'file';
  obligatoire: boolean;
  options: string[] | null;
}

interface Evenement {
  id: number;
  titre: string;
  description: string;
  statut: 'ouvert' | 'complet' | 'termine' | 'annule' | 'brouillon';
  actif: boolean;
  nombre_places: number;
  created_at: string;
}

interface InscriptionData {
  evenement: number;
  nom: string;
  prenom: string;
  email: string;
  telephone: string;
  reponses: Array<{
    champ: number;
    valeur: any;
  }>;
}

interface ApiError {
  non_field_errors?: string[];
  [field: string]: string[] | undefined;
}
```

### **Hooks React (exemple)**
```typescript
const useEvenements = () => {
  const [evenements, setEvenements] = useState<Evenement[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchEvenements = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/evenements/');
      const data = await response.json();
      setEvenements(data);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitInscription = async (data: InscriptionData, fichiers: Record<number, File>) => {
    const form = new FormData();

    form.append('evenement', data.evenement.toString());
    form.append('nom', data.nom);
    form.append('prenom', data.prenom);
    form.append('email', data.email);
    form.append('telephone', data.telephone);
    form.append('reponses', JSON.stringify(data.reponses));

    Object.entries(fichiers).forEach(([champId, file]) => {
      form.append(`fichier_champ_${champId}`, file);
    });

    const response = await fetch('/api/evenements/inscriptions/', {
      method: 'POST',
      body: form
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(Object.values(errorData).flat().join(', '));
    }

    return await response.json();
  };

  return {
    evenements,
    loading,
    fetchEvenements,
    submitInscription
  };
};
```

---

## 🎯 **Bonnes Pratiques Frontend**

### **1. Validation côté Frontend**
```javascript
const validateChamp = (champ, valeur) => {
  if (champ.obligatoire && (!valeur || valeur === '')) {
    return `${champ.label} est obligatoire`;
  }

  switch (champ.type) {
    case 'number':
      if (valeur && !/^\d*\.?\d*$/.test(valeur)) {
        return `${champ.label} doit être un nombre`;
      }
      break;
    case 'email':
      if (valeur && !/\S+@\S+\.\S+/.test(valeur)) {
        return `Email invalide`;
      }
      break;
    // ... autres validations
  }

  return null;
};
```

### **2. Gestion des Fichiers**
```javascript
const handleFileChange = (champId, file) => {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword'];

  if (file.size > maxSize) {
    return 'Fichier trop volumineux (max 10MB)';
  }

  if (!allowedTypes.includes(file.type)) {
    return 'Type de fichier non autorisé';
  }

  setFichiers(prev => ({ ...prev, [champId]: file }));
};
```

### **3. Gestion des Erreurs**
```javascript
const [errors, setErrors] = useState({});

const handleSubmit = async () => {
  try {
    setErrors({});
    await submitInscription(formData, fichiers);
    // Succès - redirection ou message
  } catch (error) {
    if (error.message.includes('non_field_errors')) {
      // Erreurs générales
      setErrors({ general: error.message });
    } else {
      // Erreurs de champs
      setErrors(JSON.parse(error.message));
    }
  }
};
```

---

## 🚀 **Checklist Développement Frontend**

- [ ] Récupération de la liste des événements
- [ ] Affichage des détails d'un événement
- [ ] Récupération des champs du formulaire
- [ ] Génération dynamique des inputs selon le type
- [ ] Validation côté frontend
- [ ] Gestion des fichiers (upload, validation, preview)
- [ ] Construction du FormData avec `reponses` JSON
- [ ] Gestion des erreurs API
- [ ] Messages de succès/confirmation
- [ ] Tests avec tous les types de champs

---

## 📞 **Support**

Si vous rencontrez des problèmes :
1. Vérifiez les logs du navigateur (Console Network)
2. Vérifiez le format des données envoyées
3. Vérifiez les types de champs dans `/api/evenements/{id}/formulaire/`
4. Testez avec des données simples d'abord

**L'API est maintenant prête pour un développement frontend fluide !** 🎉





