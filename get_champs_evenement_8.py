#!/usr/bin/env python
"""
Récupérer les vrais IDs des champs pour l'événement 8
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement

print("=== CHAMPS DISPONIBLES POUR L'ÉVÉNEMENT 8 ===")

try:
    # Récupérer l'événement 8
    evenement = Evenement.objects.get(id=8)
    print(f"Événement: {evenement.titre}")
    print(f"Actif: {evenement.actif}")
    print(f"Statut: {evenement.statut}")
    print()

    # Récupérer les champs actifs
    champs = evenement.champs.filter(actif=True).order_by('ordre')

    print(f"Nombre de champs actifs: {champs.count()}")
    print()

    print("LISTE DES CHAMPS AVEC LEURS IDs:")
    print("=" * 50)

    for champ in champs:
        print(f"ID: {champ.id}")
        print(f"Label: {champ.label}")
        print(f"Type: {champ.type}")
        print(f"Obligatoire: {champ.obligatoire}")
        if champ.type == 'select' and champ.options:
            print(f"Options: {champ.options}")
        print("-" * 30)

    print()
    print("POUR VOTRE FRONTEND - Format JSON à utiliser:")
    print("[")

    for i, champ in enumerate(champs):
        comma = "," if i < len(champs) - 1 else ""
        print(f'  {{"champ": {champ.id}, "valeur": "VOTRE_VALEUR"{comma}')

    print("]")
    print()

    print("FICHIERS: Si vous avez des champs de type 'file', utilisez:")
    champs_fichiers = champs.filter(type='file')
    if champs_fichiers:
        for champ in champs_fichiers:
            print(f"- fichier_champ_{champ.id} pour le champ '{champ.label}'")
    else:
        print("- Aucun champ fichier dans cet événement")

except Evenement.DoesNotExist:
    print("ERREUR: L'événement 8 n'existe pas!")
except Exception as e:
    print(f"ERREUR: {e}")





