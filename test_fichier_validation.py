#!/usr/bin/env python
"""
Test de validation des fichiers dans les inscriptions
"""
import os
import sys
import django
from io import BytesIO
from django.core.files.base import ContentFile

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp
from apps.evenements.serializers import InscriptionCreateSerializer

def test_validation_fichier():
    print("=== TEST VALIDATION FICHIER ===\n")

    # Créer un événement de test
    try:
        evenement = Evenement.objects.create(
            titre='Test Fichier Upload',
            nombre_places=5,
            statut='ouvert'
        )

        # Créer un champ fichier obligatoire
        champ_fichier = EvenementChamp.objects.create(
            evenement=evenement,
            label='Document requis',
            type='file',
            obligatoire=True,
            ordre=1
        )

        # Créer un champ texte optionnel
        champ_texte = EvenementChamp.objects.create(
            evenement=evenement,
            label='Commentaire',
            type='text',
            obligatoire=False,
            ordre=2
        )

        print(f"[OK] Evenement et champs crees")

    except Exception as e:
        print(f"[ERROR] Erreur creation: {e}")
        return

    # Test 1: Champ obligatoire sans fichier
    print("\n1. Test: Champ fichier obligatoire manquant")
    data1 = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Sans Fichier",
        "email": "test@example.com",
        "telephone": "0123456789",
        "reponses": [
            {"champ": champ_fichier.id, "valeur": None},  # Fichier manquant
            {"champ": champ_texte.id, "valeur": "Test commentaire"}
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=data1)
        is_valid = serializer.is_valid()
        print(f"Validation reussie: {is_valid}")
        if not is_valid:
            print(f"Erreurs: {serializer.errors}")
        else:
            print("[ERROR] La validation devrait avoir echoue!")
    except Exception as e:
        print(f"Exception attendue: {e}")

    # Test 2: Avec un fichier simulé
    print("\n2. Test: Avec fichier simulé")
    # Créer un fichier simulé
    file_content = b"Contenu de test du fichier"
    test_file = ContentFile(file_content, name='test_document.pdf')

    data2 = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Avec Fichier",
        "email": "test@example.com",
        "telephone": "0123456789",
        "reponses": [
            {"champ": champ_fichier.id, "valeur": test_file},
            {"champ": champ_texte.id, "valeur": "Test avec fichier"}
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=data2)
        is_valid = serializer.is_valid()
        print(f"Validation reussie: {is_valid}")
        if not is_valid:
            print(f"Erreurs: {serializer.errors}")
        else:
            result = serializer.save()
            print(f"[OK] Inscription creee - ID: {result['id']}")

            # Récupérer l'inscription depuis la base pour vérifier
            from apps.evenements.models import Inscription
            inscription = Inscription.objects.get(id=result['id'])

            # Vérifier que le fichier a été sauvegardé
            reponses = inscription.reponses.all()
            for reponse in reponses:
                if reponse.champ.type == 'file':
                    if reponse.valeur_fichier:
                        print(f"[OK] Fichier sauvegarde: {reponse.valeur_fichier}")
                    else:
                        print("[ERROR] Fichier non sauvegarde")

    except Exception as e:
        print(f"[ERROR] Exception inattendue: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Fichier vide
    print("\n3. Test: Fichier vide")
    empty_file = ContentFile(b"", name='empty.pdf')

    data3 = {
        "evenement": evenement.id,
        "nom": "Test",
        "prenom": "Fichier Vide",
        "email": "test@example.com",
        "telephone": "0123456789",
        "reponses": [
            {"champ": champ_fichier.id, "valeur": empty_file},
            {"champ": champ_texte.id, "valeur": "Test fichier vide"}
        ]
    }

    try:
        serializer = InscriptionCreateSerializer(data=data3)
        is_valid = serializer.is_valid()
        print(f"Validation reussie: {is_valid}")
        if not is_valid:
            print(f"Erreurs: {serializer.errors}")
    except Exception as e:
        print(f"Exception: {e}")

    # Nettoyer
    evenement.delete()
    print("\n[OK] Test termine")

if __name__ == '__main__':
    test_validation_fichier()
