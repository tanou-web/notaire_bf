#!/usr/bin/env python
"""
Test rapide pour vérifier que l'inscription aux événements fonctionne maintenant.
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp
from apps.evenements.serializers import InscriptionCreateSerializer


def test_inscription_serializer():
    """Test que le sérialiseur d'inscription fonctionne maintenant"""
    print("Test du serialiseur InscriptionCreateSerializer...")

    # Créer un événement de test avec des places
    evenement = Evenement.objects.create(
        titre="Evenement Test Inscription",
        description="Test des inscriptions",
        nombre_places=10,
        actif=True
    )

    # Créer un champ obligatoire
    champ = EvenementChamp.objects.create(
        evenement=evenement,
        label="Nom complet",
        type="text",
        obligatoire=True,
        ordre=1
    )

    # Tester la validation avec des données valides
    data = {
        'evenement': evenement.id,
        'nom': 'Dupont',
        'prenom': 'Jean',
        'email': 'jean.dupont@test.com',
        'telephone': '0123456789',
        'reponses': [
            {
                'champ': champ.id,
                'valeur': 'Jean Dupont'
            }
        ]
    }

    serializer = InscriptionCreateSerializer(data=data)

    try:
        is_valid = serializer.is_valid()
        if is_valid:
            print("SUCCES: Le serialiseur est valide")
            print(f"Donnees validees: {serializer.validated_data}")
            return True
        else:
            print(f"ERREUR: {serializer.errors}")
            return False
    except Exception as e:
        print(f"ERREUR lors de la validation: {e}")
        return False
    finally:
        # Nettoyer
        champ.delete()
        evenement.delete()


if __name__ == '__main__':
    print("Test de correction du bug d'inscription...")
    print("=" * 50)

    success = test_inscription_serializer()

    print("\n" + "=" * 50)
    if success:
        print("SUCCES: Le bug d'inscription est corrige !")
    else:
        print("ERREUR: Le bug persiste.")

    sys.exit(0 if success else 1)
