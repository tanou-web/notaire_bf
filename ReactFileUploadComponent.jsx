import React, { useState, useRef } from 'react';

const API_BASE = 'https://notaire-bf-1ns8.onrender.com/api/evenements';

const FileUploadField = ({ champ, value, fichier, onChange, error }) => {
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files[0];

    if (selectedFile) {
      // Validation du fichier
      const validationError = validateFile(selectedFile);
      if (validationError) {
        alert(validationError);
        // Reset de l'input
        event.target.value = '';
        return;
      }

      onChange(champ.id, selectedFile);
    }
  };

  const handleRemove = () => {
    // Reset de l'input HTML
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onChange(champ.id, null);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`field-group file-upload-group ${error ? 'error' : ''}`}>
      <label htmlFor={`champ_${champ.id}`}>
        {champ.label}
        {champ.obligatoire ? ' *' : ' (optionnel)'}
      </label>

      <div className="file-upload-container">
        {/* Input file caché */}
        <input
          ref={fileInputRef}
          type="file"
          id={`champ_${champ.id}`}
          accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {/* Bouton de sélection OU aperçu du fichier */}
        {!fichier ? (
          <button
            type="button"
            className="file-select-button"
            onClick={handleButtonClick}
          >
            📎 Choisir un fichier
          </button>
        ) : (
          <div className="file-preview">
            <div className="file-info">
              <div className="file-icon">📄</div>
              <div className="file-details">
                <div className="file-name">{fichier.name}</div>
                <div className="file-size">{formatFileSize(fichier.size)}</div>
              </div>
            </div>
            <button
              type="button"
              className="file-remove-button"
              onClick={handleRemove}
              title="Supprimer le fichier"
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Aide et informations */}
      <div className="file-help">
        <small>
          Formats acceptés : PDF, JPG, PNG, DOC, DOCX<br />
          Taille maximale : 10 MB
        </small>
      </div>

      {/* Message d'erreur */}
      {error && <div className="field-error">{error}</div>}
    </div>
  );
};

// Fonction de validation des fichiers
const validateFile = (file) => {
  // Taille maximale : 10MB
  const maxSize = 10 * 1024 * 1024; // 10MB en bytes
  if (file.size > maxSize) {
    return `Le fichier est trop volumineux (${formatFileSize(file.size)}). La taille maximale autorisée est de 10 MB.`;
  }

  // Extensions autorisées
  const allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'];
  const fileName = file.name.toLowerCase();
  const fileExtension = fileName.substring(fileName.lastIndexOf('.'));

  if (!allowedExtensions.includes(fileExtension)) {
    return `Extension de fichier non autorisée : ${fileExtension}. Les extensions acceptées sont : ${allowedExtensions.join(', ')}.`;
  }

  // Vérifier que le fichier n'est pas vide
  if (file.size === 0) {
    return 'Le fichier sélectionné est vide.';
  }

  return null; // Pas d'erreur
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default FileUploadField;
