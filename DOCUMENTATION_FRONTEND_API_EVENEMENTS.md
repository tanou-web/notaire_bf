# 📋 Documentation Frontend - API Événements Notaires BF

## 🎯 Vue d'ensemble

L'API des événements permet aux utilisateurs de :
- Consulter les événements disponibles
- S'inscrire aux événements avec des formulaires dynamiques
- Uploader des fichiers lors de l'inscription

**Base URL :** `https://notaire-bf-1ns8.onrender.com/api/evenements/`

---

## 📚 Endpoints Disponibles

### 1. Liste des événements
```http
GET /api/evenements/evenements/
```

**Réponse :**
```json
[
  {
    "id": 1,
    "titre": "Conférence Droit Immobilier",
    "description": "Conférence sur les dernières évolutions",
    "statut": "ouvert",
    "actif": true,
    "nombre_places": 50,
    "created_at": "2024-01-24T10:00:00Z",
    "champs": [
      {
        "id": 1,
        "label": "Profession",
        "type": "text",
        "obligatoire": true,
        "ordre": 1,
        "options": null,
        "actif": true
      }
    ]
  }
]
```

### 2. Détails d'un événement
```http
GET /api/evenements/evenements/{id}/
```

### 3. Formulaire d'inscription
```http
GET /api/evenements/evenements/{id}/formulaire/
```

**Réponse :**
```json
{
  "evenement": 1,
  "formulaire": [
    {
      "id": 1,
      "label": "Nom complet",
      "type": "text",
      "obligatoire": true,
      "options": null
    },
    {
      "id": 2,
      "label": "Âge",
      "type": "number",
      "obligatoire": false,
      "options": null
    },
    {
      "id": 3,
      "label": "Profession",
      "type": "select",
      "obligatoire": true,
      "options": ["Avocat", "Notaire", "Consultant"]
    },
    {
      "id": 4,
      "label": "Date de naissance",
      "type": "date",
      "obligatoire": false,
      "options": null
    },
    {
      "id": 5,
      "label": "Accepte conditions",
      "type": "checkbox",
      "obligatoire": true,
      "options": null
    },
    {
      "id": 6,
      "label": "CV",
      "type": "file",
      "obligatoire": false,
      "options": null
    }
  ]
}
```

### 4. Créer une inscription
```http
POST /api/evenements/inscriptions/
```

**⚠️ IMPORTANT :** Utilise `FormData` pour les fichiers !

---

## 🔧 Types de champs supportés

| Type | Description | Valeur attendue | Validation |
|------|-------------|-----------------|------------|
| `text` | Champ texte simple | `string` | Longueur max 255 |
| `textarea` | Zone de texte | `string` | Longueur max 1000 |
| `number` | Nombre | `number` | Décimal optionnel |
| `date` | Date | `string` | `AAAA-MM-JJ` ou `JJ/MM/AAAA` |
| `checkbox` | Case à cocher | `boolean` | `true` ou `false` |
| `select` | Liste déroulante | `string` | Doit être dans `options` |
| `file` | Upload de fichier | `File` | Max 10MB, extensions limitées |

---

## 📝 Exemples d'utilisation

### Configuration de base
```javascript
const API_BASE = 'https://notaire-bf-1ns8.onrender.com/api/evenements';
```

### 1. Charger les événements disponibles
```javascript
async function loadEvenements() {
  try {
    const response = await fetch(`${API_BASE}/evenements/`);
    const evenements = await response.json();

    // Filtrer les événements ouverts et actifs
    const evenementsDisponibles = evenements.filter(
      event => event.actif && event.statut === 'ouvert'
    );

    return evenementsDisponibles;
  } catch (error) {
    console.error('Erreur chargement événements:', error);
    throw error;
  }
}
```

### 2. Charger le formulaire d'un événement
```javascript
async function loadFormulaire(evenementId) {
  try {
    const response = await fetch(`${API_BASE}/evenements/${evenementId}/formulaire/`);
    const data = await response.json();

    // Trier les champs par ordre
    const champs = data.formulaire.sort((a, b) => a.ordre - b.ordre);

    return {
      evenementId: data.evenement,
      champs: champs
    };
  } catch (error) {
    console.error('Erreur chargement formulaire:', error);
    throw error;
  }
}
```

### 3. Soumettre une inscription SANS fichiers
```javascript
async function soumettreInscriptionSimple(inscriptionData) {
  try {
    const formData = new FormData();

    // Champs principaux
    formData.append('evenement', inscriptionData.evenementId);
    formData.append('nom', inscriptionData.nom);
    formData.append('prenom', inscriptionData.prenom);
    formData.append('email', inscriptionData.email);
    formData.append('telephone', inscriptionData.telephone);

    // Réponses aux champs dynamiques
    const reponses = inscriptionData.champs.map(champ => ({
      champ: champ.id,
      valeur: champ.valeur
    }));
    formData.append('reponses', JSON.stringify(reponses));

    const response = await fetch(`${API_BASE}/inscriptions/`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Erreur ${response.status}: ${JSON.stringify(errorData)}`);
    }

    const result = await response.json();
    return result;

  } catch (error) {
    console.error('Erreur soumission:', error);
    throw error;
  }
}
```

### 4. Soumettre une inscription AVEC fichiers
```javascript
async function soumettreInscriptionAvecFichiers(inscriptionData) {
  try {
    const formData = new FormData();

    // Champs principaux
    formData.append('evenement', inscriptionData.evenementId);
    formData.append('nom', inscriptionData.nom);
    formData.append('prenom', inscriptionData.prenom);
    formData.append('email', inscriptionData.email);
    formData.append('telephone', inscriptionData.telephone);

    // Traiter les réponses et fichiers
    const reponses = [];
    inscriptionData.champs.forEach(champ => {
      if (champ.type === 'file' && champ.fichier) {
        // Pour les fichiers : nom dans valeur, fichier séparé
        reponses.push({
          champ: champ.id,
          valeur: champ.fichier.name
        });
        formData.append(`fichier_champ_${champ.id}`, champ.fichier);
      } else {
        // Pour les autres champs
        reponses.push({
          champ: champ.id,
          valeur: champ.valeur
        });
      }
    });

    formData.append('reponses', JSON.stringify(reponses));

    const response = await fetch(`${API_BASE}/inscriptions/`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Erreur ${response.status}`;

      try {
        const errorData = JSON.parse(errorText);
        errorMessage += `: ${JSON.stringify(errorData)}`;
      } catch {
        errorMessage += `: ${errorText}`;
      }

      throw new Error(errorMessage);
    }

    const result = await response.json();
    return result;

  } catch (error) {
    console.error('Erreur soumission avec fichiers:', error);
    throw error;
  }
}
```

### 5. Gestion des dates
```javascript
// Conversion de date pour l'affichage
function formatDateForDisplay(dateString) {
  if (!dateString) return '';

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR'); // JJ/MM/AAAA
  } catch {
    return dateString;
  }
}

// Conversion de date pour l'envoi
function formatDateForAPI(dateString) {
  if (!dateString) return '';

  try {
    // Si c'est déjà au format ISO, garder tel quel
    if (dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateString;
    }

    // Convertir JJ/MM/AAAA vers AAAA-MM-JJ
    const [day, month, year] = dateString.split('/');
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  } catch {
    return dateString;
  }
}
```

---

## 🎨 Composant React d'exemple

```jsx
import React, { useState, useEffect } from 'react';

const InscriptionEvenement = ({ evenementId }) => {
  const [evenement, setEvenement] = useState(null);
  const [formulaire, setFormulaire] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [soumission, setSoumission] = useState(false);
  const [erreur, setErreur] = useState(null);
  const [succes, setSucces] = useState(false);

  // État du formulaire
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    champs: {}
  });

  // Charger les données
  useEffect(() => {
    const loadData = async () => {
      try {
        // Charger l'événement
        const eventResponse = await fetch(`/api/evenements/evenements/${evenementId}/`);
        const eventData = await eventResponse.json();
        setEvenement(eventData);

        // Charger le formulaire
        const formResponse = await fetch(`/api/evenements/evenements/${evenementId}/formulaire/`);
        const formData = await formResponse.json();
        setFormulaire(formData.formulaire);

        // Initialiser l'état des champs
        const champsInit = {};
        formData.formulaire.forEach(champ => {
          champsInit[champ.id] = {
            id: champ.id,
            type: champ.type,
            valeur: '',
            fichier: null
          };
        });
        setFormData(prev => ({ ...prev, champs: champsInit }));

      } catch (error) {
        setErreur('Erreur de chargement des données');
        console.error(error);
      } finally {
        setChargement(false);
      }
    };

    loadData();
  }, [evenementId]);

  // Gestionnaire de changement
  const handleChange = (champId, valeur, fichier = null) => {
    setFormData(prev => ({
      ...prev,
      champs: {
        ...prev.champs,
        [champId]: {
          ...prev.champs[champId],
          valeur: valeur,
          fichier: fichier
        }
      }
    }));
  };

  // Soumission du formulaire
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSoumission(true);
    setErreur(null);

    try {
      const formDataToSend = new FormData();

      // Champs principaux
      formDataToSend.append('evenement', evenementId);
      formDataToSend.append('nom', formData.nom);
      formDataToSend.append('prenom', formData.prenom);
      formDataToSend.append('email', formData.email);
      formDataToSend.append('telephone', formData.telephone);

      // Traiter les réponses
      const reponses = [];
      Object.values(formData.champs).forEach(champ => {
        if (champ.type === 'file' && champ.fichier) {
          reponses.push({
            champ: champ.id,
            valeur: champ.fichier.name
          });
          formDataToSend.append(`fichier_champ_${champ.id}`, champ.fichier);
        } else {
          reponses.push({
            champ: champ.id,
            valeur: champ.valeur
          });
        }
      });

      formDataToSend.append('reponses', JSON.stringify(reponses));

      const response = await fetch('/api/evenements/inscriptions/', {
        method: 'POST',
        body: formDataToSend
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(JSON.stringify(errorData));
      }

      const result = await response.json();
      setSucces(true);
      console.log('Inscription réussie:', result);

    } catch (error) {
      setErreur(error.message);
      console.error('Erreur soumission:', error);
    } finally {
      setSoumission(false);
    }
  };

  if (chargement) {
    return <div>Chargement...</div>;
  }

  if (succes) {
    return (
      <div className="success">
        <h2>Inscription réussie !</h2>
        <p>Vous recevrez bientôt une confirmation par email.</p>
      </div>
    );
  }

  return (
    <div className="inscription-form">
      <h1>Inscription à {evenement?.titre}</h1>

      {erreur && (
        <div className="error">
          <strong>Erreur :</strong> {erreur}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Champs principaux */}
        <div className="field-group">
          <label>Nom *</label>
          <input
            type="text"
            value={formData.nom}
            onChange={(e) => setFormData(prev => ({ ...prev, nom: e.target.value }))}
            required
          />
        </div>

        <div className="field-group">
          <label>Prénom *</label>
          <input
            type="text"
            value={formData.prenom}
            onChange={(e) => setFormData(prev => ({ ...prev, prenom: e.target.value }))}
            required
          />
        </div>

        <div className="field-group">
          <label>Email *</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            required
          />
        </div>

        <div className="field-group">
          <label>Téléphone *</label>
          <input
            type="tel"
            value={formData.telephone}
            onChange={(e) => setFormData(prev => ({ ...prev, telephone: e.target.value }))}
            required
          />
        </div>

        {/* Champs dynamiques */}
        {formulaire.map(champ => (
          <div key={champ.id} className="field-group">
            <label>
              {champ.label}
              {champ.obligatoire && ' *'}
            </label>

            {champ.type === 'text' && (
              <input
                type="text"
                value={formData.champs[champ.id]?.valeur || ''}
                onChange={(e) => handleChange(champ.id, e.target.value)}
                required={champ.obligatoire}
              />
            )}

            {champ.type === 'textarea' && (
              <textarea
                value={formData.champs[champ.id]?.valeur || ''}
                onChange={(e) => handleChange(champ.id, e.target.value)}
                required={champ.obligatoire}
              />
            )}

            {champ.type === 'number' && (
              <input
                type="number"
                value={formData.champs[champ.id]?.valeur || ''}
                onChange={(e) => handleChange(champ.id, e.target.value)}
                required={champ.obligatoire}
              />
            )}

            {champ.type === 'date' && (
              <input
                type="date"
                value={formData.champs[champ.id]?.valeur || ''}
                onChange={(e) => handleChange(champ.id, e.target.value)}
                required={champ.obligatoire}
              />
            )}

            {champ.type === 'checkbox' && (
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.champs[champ.id]?.valeur || false}
                  onChange={(e) => handleChange(champ.id, e.target.checked)}
                  required={champ.obligatoire}
                />
                {champ.label}
              </label>
            )}

            {champ.type === 'select' && (
              <select
                value={formData.champs[champ.id]?.valeur || ''}
                onChange={(e) => handleChange(champ.id, e.target.value)}
                required={champ.obligatoire}
              >
                <option value="">Choisir...</option>
                {champ.options?.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            )}

            {champ.type === 'file' && (
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={(e) => {
                  const file = e.target.files[0];
                  handleChange(champ.id, file?.name || '', file);
                }}
                required={champ.obligatoire}
              />
            )}
          </div>
        ))}

        <button type="submit" disabled={soumission}>
          {soumission ? 'Inscription en cours...' : 'S\'inscrire'}
        </button>
      </form>
    </div>
  );
};

export default InscriptionEvenement;
```

---

## 🚨 Gestion des erreurs

### Types d'erreurs courants

| Code HTTP | Signification | Action |
|-----------|---------------|--------|
| `400` | Données invalides | Vérifier les champs requis et formats |
| `404` | Événement introuvable | Vérifier l'ID de l'événement |
| `413` | Fichier trop volumineux | Réduire la taille du fichier (< 10MB) |
| `415` | Type de contenu invalide | Utiliser FormData pour les fichiers |
| `422` | Validation échouée | Corriger les données selon les messages d'erreur |
| `500` | Erreur serveur | Signaler à l'équipe technique |

### Structure des erreurs API

```json
{
  "evenement": ["Ce champ est obligatoire."],
  "nom": ["Ce champ est obligatoire."],
  "email": ["Adresse email invalide."],
  "reponses": ["Champ 5 est obligatoire"],
  "non_field_errors": ["Format de date invalide pour Date de naissance"]
}
```

### Gestion des erreurs en JavaScript

```javascript
const handleApiError = (error, response) => {
  if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
    // Problème de réseau
    return 'Erreur de connexion. Vérifiez votre connexion internet.';
  }

  if (response) {
    const status = response.status;

    if (status === 400) {
      // Erreur de validation
      return 'Veuillez corriger les erreurs dans le formulaire.';
    }

    if (status === 413) {
      return 'Le fichier est trop volumineux (maximum 10MB).';
    }

    if (status === 415) {
      return 'Erreur d\'envoi des fichiers. Actualisez la page.';
    }

    if (status >= 500) {
      return 'Erreur serveur. Réessayez plus tard.';
    }
  }

  return 'Une erreur inattendue s\'est produite.';
};
```

---

## 🔒 Bonnes pratiques

### 1. Validation côté client
```javascript
const validateForm = (formData, formulaire) => {
  const errors = {};

  // Validation des champs principaux
  if (!formData.nom.trim()) errors.nom = 'Le nom est requis';
  if (!formData.prenom.trim()) errors.prenom = 'Le prénom est requis';
  if (!formData.email.includes('@')) errors.email = 'Email invalide';
  if (!formData.telephone.trim()) errors.telephone = 'Téléphone requis';

  // Validation des champs dynamiques
  formulaire.forEach(champ => {
    const valeur = formData.champs[champ.id]?.valeur;

    if (champ.obligatoire && !valeur) {
      errors[champ.id] = `${champ.label} est requis`;
    }

    if (champ.type === 'email' && valeur && !valeur.includes('@')) {
      errors[champ.id] = 'Format email invalide';
    }

    if (champ.type === 'file' && champ.obligatoire && !formData.champs[champ.id]?.fichier) {
      errors[champ.id] = `Le fichier ${champ.label} est requis`;
    }
  });

  return errors;
};
```

### 2. Gestion du chargement
```javascript
const [etat, setEtat] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'

const submitForm = async () => {
  setEtat('loading');

  try {
    await submitToAPI(formData);
    setEtat('success');
  } catch (error) {
    setEtat('error');
    // Gérer l'erreur
  }
};
```

### 3. Upload progress (optionnel)
```javascript
const uploadWithProgress = async (formData, onProgress) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percent = (event.loaded / event.total) * 100;
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Erreur réseau'));
    });

    xhr.open('POST', '/api/evenements/inscriptions/');
    xhr.send(formData);
  });
};
```

---

## 📋 Checklist intégration

- [ ] Endpoint `/evenements/` appelé pour lister les événements
- [ ] Endpoint `/evenements/{id}/formulaire/` appelé pour charger les champs
- [ ] Champs triés par ordre d'affichage
- [ ] Validation des champs obligatoires
- [ ] Gestion des différents types de champs (text, number, date, select, checkbox, file)
- [ ] Utilisation de FormData pour les uploads de fichiers
- [ ] Gestion des erreurs API (400, 413, 415, 500)
- [ ] Messages d'erreur user-friendly
- [ ] États de chargement et succès
- [ ] Validation côté client avant soumission
- [ ] Support des formats de date français et ISO

---

## 🆘 Support et débogage

### Outils de débogage
```javascript
// Debug FormData
const debugFormData = (formData) => {
  console.log('=== FORM DATA DEBUG ===');
  for (let [key, value] of formData.entries()) {
    if (value instanceof File) {
      console.log(`${key}: File(${value.name}, ${value.size} bytes)`);
    } else {
      console.log(`${key}: ${value}`);
    }
  }
};

// Debug réponse API
const debugApiResponse = async (response) => {
  console.log('=== API RESPONSE DEBUG ===');
  console.log('Status:', response.status);
  console.log('Headers:', Object.fromEntries(response.headers.entries()));

  const text = await response.text();
  try {
    const json = JSON.parse(text);
    console.log('Body:', json);
  } catch {
    console.log('Body (text):', text);
  }
};
```

### Tests manuels avec cURL
```bash
# Test liste événements
curl -X GET "https://notaire-bf-1ns8.onrender.com/api/evenements/evenements/"

# Test formulaire
curl -X GET "https://notaire-bf-1ns8.onrender.com/api/evenements/evenements/1/formulaire/"

# Test inscription simple
curl -X POST "https://notaire-bf-1ns8.onrender.com/api/evenements/inscriptions/" \
  -F "evenement=1" \
  -F "nom=Test" \
  -F "prenom=User" \
  -F "email=test@example.com" \
  -F "telephone=0123456789" \
  -F "reponses=[{\"champ\":1,\"valeur\":\"Test\"}]"
```

---

*Documentation créée pour les développeurs frontend - API Événements Notaires BF* 📚✨
