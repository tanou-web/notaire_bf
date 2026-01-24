import React, { useState, useEffect } from 'react';
import FileUploadField from './FileUploadField';

const API_BASE = 'https://notaire-bf-1ns8.onrender.com/api/evenements';

const InscriptionForm = ({ evenementId }) => {
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
    champs: {} // Contiendra les valeurs des champs dynamiques
  });

  // Charger le formulaire au montage
  useEffect(() => {
    loadFormulaire();
  }, [evenementId]);

  const loadFormulaire = async () => {
    try {
      const response = await fetch(`${API_BASE}/evenements/${evenementId}/formulaire/`);
      if (!response.ok) throw new Error('Erreur chargement formulaire');

      const data = await response.json();
      const champs = data.formulaire.sort((a, b) => a.ordre - b.ordre);

      setFormulaire(champs);

      // Initialiser l'état des champs dynamiques
      const champsInit = {};
      champs.forEach(champ => {
        champsInit[champ.id] = {
          id: champ.id,
          type: champ.type,
          valeur: '',
          fichier: null,
          erreur: null
        };
      });

      setFormData(prev => ({ ...prev, champs: champsInit }));

    } catch (error) {
      setErreur('Impossible de charger le formulaire');
      console.error(error);
    } finally {
      setChargement(false);
    }
  };

  // Gestionnaire pour les champs texte normaux
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Gestionnaire pour les champs dynamiques
  const handleChampChange = (champId, value, fichier = null) => {
    setFormData(prev => ({
      ...prev,
      champs: {
        ...prev.champs,
        [champId]: {
          ...prev.champs[champId],
          valeur: fichier ? fichier.name : value,
          fichier: fichier,
          erreur: null
        }
      }
    }));
  };

  // Validation du formulaire
  const validateForm = () => {
    const errors = {};

    // Validation des champs principaux
    if (!formData.nom.trim()) errors.nom = 'Le nom est requis';
    if (!formData.prenom.trim()) errors.prenom = 'Le prénom est requis';
    if (!formData.email.trim()) errors.email = 'L\'email est requis';
    if (!formData.email.includes('@')) errors.email = 'Format d\'email invalide';
    if (!formData.telephone.trim()) errors.telephone = 'Le téléphone est requis';

    // Validation des champs dynamiques
    formulaire.forEach(champ => {
      const champData = formData.champs[champ.id];

      if (champ.obligatoire) {
        if (champ.type === 'file') {
          if (!champData?.fichier) {
            errors[champ.id] = `${champ.label} est requis`;
          }
        } else if (!champData?.valeur?.trim()) {
          errors[champ.id] = `${champ.label} est requis`;
        }
      }

      // Validation spécifique par type
      if (champ.type === 'email' && champData?.valeur && !champData.valeur.includes('@')) {
        errors[champ.id] = 'Format d\'email invalide';
      }

      if (champ.type === 'number' && champData?.valeur) {
        if (isNaN(champData.valeur)) {
          errors[champ.id] = `${champ.label} doit être un nombre`;
        }
      }
    });

    return errors;
  };

  // Préparation des FormData pour l'envoi
  const prepareFormData = () => {
    const formDataToSend = new FormData();

    // Champs principaux
    formDataToSend.append('evenement', evenementId);
    formDataToSend.append('nom', formData.nom);
    formDataToSend.append('prenom', formData.prenom);
    formDataToSend.append('email', formData.email);
    formDataToSend.append('telephone', formData.telephone);

    // Construction des réponses
    const reponses = [];
    Object.values(formData.champs).forEach(champ => {
      if (champ.type === 'file' && champ.fichier) {
        // Pour les fichiers : nom dans valeur, fichier séparé
        reponses.push({
          champ: champ.id,
          valeur: champ.fichier.name
        });

        // Ajouter le fichier avec la clé spéciale
        formDataToSend.append(`fichier_champ_${champ.id}`, champ.fichier);

      } else {
        // Pour les autres champs
        reponses.push({
          champ: champ.id,
          valeur: champ.valeur
        });
      }
    });

    // Ajouter les réponses en JSON
    formDataToSend.append('reponses', JSON.stringify(reponses));

    return formDataToSend;
  };

  // Soumission du formulaire
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      // Marquer les erreurs dans l'état
      setFormData(prev => {
        const newChamps = { ...prev.champs };
        Object.keys(errors).forEach(key => {
          if (key in newChamps) {
            newChamps[key] = { ...newChamps[key], erreur: errors[key] };
          }
        });
        return { ...prev, champs: newChamps };
      });

      setErreur('Veuillez corriger les erreurs dans le formulaire');
      return;
    }

    setSoumission(true);
    setErreur(null);

    try {
      const formDataToSend = prepareFormData();

      // Debug : afficher le contenu du FormData
      console.log('=== FORM DATA DEBUG ===');
      for (let [key, value] of formDataToSend.entries()) {
        if (value instanceof File) {
          console.log(`${key}: File(${value.name}, ${value.size} bytes)`);
        } else {
          console.log(`${key}: ${value}`);
        }
      }

      const response = await fetch(`${API_BASE}/inscriptions/`, {
        method: 'POST',
        body: formDataToSend // PAS de Content-Type !
      });

      if (!response.ok) {
        let errorMessage = `Erreur ${response.status}`;

        try {
          const errorData = await response.json();
          console.error('Détails erreur:', errorData);

          // Gérer les erreurs de validation spécifiques
          if (response.status === 400 && errorData.non_field_errors) {
            errorMessage = errorData.non_field_errors.join(', ');
          } else if (response.status === 413) {
            errorMessage = 'Fichier trop volumineux (maximum 10MB)';
          } else if (response.status === 415) {
            errorMessage = 'Erreur d\'envoi des fichiers';
          }

        } catch {
          const errorText = await response.text();
          console.error('Erreur texte:', errorText);
        }

        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('✅ Inscription réussie:', result);
      setSucces(true);

    } catch (error) {
      console.error('❌ Erreur soumission:', error);
      setErreur(error.message);
    } finally {
      setSoumission(false);
    }
  };

  // Affichage du chargement
  if (chargement) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Chargement du formulaire...</p>
      </div>
    );
  }

  // Affichage du succès
  if (succes) {
    return (
      <div className="success-message">
        <div className="success-icon">✅</div>
        <h2>Inscription réussie !</h2>
        <p>Votre inscription a été enregistrée avec succès.</p>
        <p>Vous recevrez bientôt une confirmation par email.</p>
      </div>
    );
  }

  return (
    <div className="inscription-form">
      <h1>Formulaire d'inscription</h1>

      {erreur && (
        <div className="error-message">
          <strong>Erreur :</strong> {erreur}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Champs principaux */}
        <div className="form-section">
          <h3>Informations personnelles</h3>

          <div className="field-row">
            <div className="field-group">
              <label htmlFor="nom">Nom *</label>
              <input
                type="text"
                id="nom"
                value={formData.nom}
                onChange={(e) => handleInputChange('nom', e.target.value)}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="prenom">Prénom *</label>
              <input
                type="text"
                id="prenom"
                value={formData.prenom}
                onChange={(e) => handleInputChange('prenom', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="field-row">
            <div className="field-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="telephone">Téléphone *</label>
              <input
                type="tel"
                id="telephone"
                value={formData.telephone}
                onChange={(e) => handleInputChange('telephone', e.target.value)}
                required
              />
            </div>
          </div>
        </div>

        {/* Champs dynamiques */}
        {formulaire.length > 0 && (
          <div className="form-section">
            <h3>Informations supplémentaires</h3>

            {formulaire.map(champ => {
              const champData = formData.champs[champ.id];

              return (
                <div key={champ.id}>
                  {champ.type === 'file' ? (
                    <FileUploadField
                      champ={champ}
                      value={champData?.valeur || ''}
                      fichier={champData?.fichier}
                      onChange={handleChampChange}
                      error={champData?.erreur}
                    />
                  ) : (
                    <div className={`field-group ${champData?.erreur ? 'error' : ''}`}>
                      <label htmlFor={`champ_${champ.id}`}>
                        {champ.label}
                        {champ.obligatoire ? ' *' : ' (optionnel)'}
                      </label>

                      {champ.type === 'text' && (
                        <input
                          type="text"
                          id={`champ_${champ.id}`}
                          value={champData?.valeur || ''}
                          onChange={(e) => handleChampChange(champ.id, e.target.value)}
                          required={champ.obligatoire}
                        />
                      )}

                      {champ.type === 'textarea' && (
                        <textarea
                          id={`champ_${champ.id}`}
                          value={champData?.valeur || ''}
                          onChange={(e) => handleChampChange(champ.id, e.target.value)}
                          required={champ.obligatoire}
                        />
                      )}

                      {champ.type === 'number' && (
                        <input
                          type="number"
                          id={`champ_${champ.id}`}
                          value={champData?.valeur || ''}
                          onChange={(e) => handleChampChange(champ.id, e.target.value)}
                          required={champ.obligatoire}
                        />
                      )}

                      {champ.type === 'date' && (
                        <input
                          type="date"
                          id={`champ_${champ.id}`}
                          value={champData?.valeur || ''}
                          onChange={(e) => handleChampChange(champ.id, e.target.value)}
                          required={champ.obligatoire}
                        />
                      )}

                      {champ.type === 'checkbox' && (
                        <label className="checkbox-label">
                          <input
                            type="checkbox"
                            id={`champ_${champ.id}`}
                            checked={champData?.valeur || false}
                            onChange={(e) => handleChampChange(champ.id, e.target.checked)}
                            required={champ.obligatoire}
                          />
                          {champ.label}
                        </label>
                      )}

                      {champ.type === 'select' && (
                        <select
                          id={`champ_${champ.id}`}
                          value={champData?.valeur || ''}
                          onChange={(e) => handleChampChange(champ.id, e.target.value)}
                          required={champ.obligatoire}
                        >
                          <option value="">Choisir...</option>
                          {champ.options?.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      )}

                      {champData?.erreur && (
                        <div className="field-error">{champData.erreur}</div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={soumission}
            className="submit-button"
          >
            {soumission ? 'Inscription en cours...' : 'S\'inscrire'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default InscriptionForm;
