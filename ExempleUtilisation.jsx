// Exemple d'utilisation des composants React pour les inscriptions d'événements

import React from 'react';
import InscriptionForm from './ReactInscriptionForm';
import './InscriptionForm.css';

function App() {
  return (
    <div className="app">
      <header>
        <h1>Inscription aux Événements</h1>
      </header>

      <main>
        {/* Formulaire pour l'événement ID 8 */}
        <InscriptionForm evenementId={8} />
      </main>
    </div>
  );
}

// Si vous voulez charger dynamiquement l'ID de l'événement depuis l'URL
import { useParams } from 'react-router-dom';

function PageInscription() {
  const { evenementId } = useParams();

  return (
    <div className="page-inscription">
      <InscriptionForm evenementId={parseInt(evenementId)} />
    </div>
  );
}

// Exemple avec gestion d'erreur globale
import { useState } from 'react';

function AppWithErrorHandling() {
  const [error, setError] = useState(null);

  // Intercepter les erreurs globales si nécessaire
  React.useEffect(() => {
    const handleError = (event) => {
      console.error('Erreur globale:', event.error);
      setError('Une erreur inattendue s\'est produite');
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  return (
    <div className="app">
      {error && (
        <div className="global-error">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Fermer</button>
        </div>
      )}

      <InscriptionForm evenementId={8} />
    </div>
  );
}

export default App;
