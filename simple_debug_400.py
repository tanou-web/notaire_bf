#!/usr/bin/env python
"""
Debug simple de l'erreur 400
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Evenement, EvenementChamp

print("=== DEBUG ERREUR 400 ===")

# Vérifier l'événement 8
print("\n1. Evenement 8:")
try:
    event = Evenement.objects.get(id=8)
    print(f"   OK: {event.titre} - actif: {event.actif} - statut: {event.statut}")
except Evenement.DoesNotExist:
    print("   ERREUR: Evenement 8 n'existe pas!")

# Vérifier les champs utilisés
print("\n2. Champs utilises:")
champ_ids = [8, 9, 10, 11, 12, 13, 39]

for champ_id in champ_ids:
    try:
        champ = EvenementChamp.objects.get(id=champ_id, evenement_id=8, actif=True)
        print(f"   OK: Champ {champ_id} - {champ.label} ({champ.type}) - oblig: {champ.obligatoire}")
        if champ.type == 'select' and champ.options:
            print(f"       Options: {champ.options}")
    except EvenementChamp.DoesNotExist:
        print(f"   ERREUR: Champ {champ_id} n'existe pas ou inactif!")

print("\n3. Analyse des donnees envoyees:")
print("   - evenement: 8")
print("   - nom: Bngo")
print("   - prenom: Dems")
print("   - email: clovdesign14@gmail.com")
print("   - telephone: 53169736")
print("   - fichier: fichier_champ_39")

print("\n   Reponses JSON:")
reponses = [
    {"champ":8,"valeur":"Dems Bngo"},
    {"champ":9,"valeur":74},
    {"champ":10,"valeur":"Avocat"},
    {"champ":11,"valeur":"Dems"},
    {"champ":12,"valeur":"14/11/2016"},
    {"champ":13,"valeur":True},
    {"champ":39,"valeur":"0540-tutoriel-sur-laravel.pdf"}
]

for rep in reponses:
    champ_id = rep['champ']
    valeur = rep['valeur']
    try:
        champ = EvenementChamp.objects.get(id=champ_id, evenement_id=8, actif=True)
        print(f"     Champ {champ_id} ({champ.type}): '{valeur}' -> ", end="")

        # Validation simple
        if champ.type == 'select' and champ.options:
            if valeur not in champ.options:
                print(f"ERREUR: '{valeur}' pas dans {champ.options}")
            else:
                print("OK")
        elif champ.type == 'date':
            # Tester les formats de date
            from datetime import datetime
            try:
                datetime.strptime(str(valeur), '%d/%m/%Y')
                print("OK (format francais)")
            except:
                try:
                    datetime.strptime(str(valeur), '%Y-%m-%d')
                    print("OK (format ISO)")
                except:
                    print(f"ERREUR: Format date invalide '{valeur}'")
        else:
            print("OK")

    except EvenementChamp.DoesNotExist:
        print(f"     Champ {champ_id}: ERREUR - champ inexistant")

print("\n4. Causes possibles de l'erreur 400:")
print("   - Evenement 8 n'existe pas")
print("   - Un champ n'existe pas ou est inactif")
print("   - Valeur select pas dans les options")
print("   - Format de date invalide")
print("   - Fichier trop volumineux ou extension invalide")
print("   - Champ obligatoire manquant")








