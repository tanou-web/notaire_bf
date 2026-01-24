#!/usr/bin/env python
"""
Vérifier si les réponses sont bien sauvegardées en base de données
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.evenements.models import Inscription, InscriptionReponse

def verifier_reponses():
    print("=== VÉRIFICATION DES RÉPONSES SAUVEGARDÉES ===\n")

    # Chercher l'inscription récente (celle de "Bngo Dems")
    try:
        inscription = Inscription.objects.filter(
            nom="Bngo",
            prenom="Dems",
            email="clovdesign14@gmail.com"
        ).first()

        if not inscription:
            print("[ERROR] Aucune inscription trouvee pour 'Bngo Dems'")
            return

        print(f"[OK] Inscription trouvee: ID {inscription.id}")
        print(f"   Evenement: {inscription.evenement.id} - {inscription.evenement.titre}")
        print(f"   Nom: {inscription.nom} {inscription.prenom}")
        print(f"   Email: {inscription.email}")
        print(f"   Telephone: {inscription.telephone}")
        print(f"   Statut: {inscription.statut}")
        print(f"   Date: {inscription.created_at}")

        # Vérifier les réponses
        reponses = inscription.reponses.all()
        print(f"\n[INFO] Reponses sauvegardees: {reponses.count()}")

        if reponses.count() == 0:
            print("[ERROR] AUCUNE REPONSE SAUVEGARDEE !")
            return

        print("\n[INFO] Detail des reponses:")
        for i, reponse in enumerate(reponses, 1):
            valeur = None
            if reponse.valeur_texte:
                valeur = f"'{reponse.valeur_texte}'"
            elif reponse.valeur_nombre is not None:
                valeur = reponse.valeur_nombre
            elif reponse.valeur_date is not None:
                valeur = reponse.valeur_date
            elif reponse.valeur_bool is not None:
                valeur = reponse.valeur_bool
            elif reponse.valeur_fichier:
                valeur = f"Fichier: {reponse.valeur_fichier}"

            print(f"   {i}. {reponse.champ.label} ({reponse.champ.type}): {valeur}")

        # Comparer avec les données envoyées
        print(f"\n[CHECK] Comparaison avec les donnees envoyees:")
        donnees_envoyees = {
            8: "Dems Bngo",
            9: 12,
            10: "Avocat",
            11: "EZEZEED",
            12: "14/11/2016",
            13: True
        }

        reponses_dict = {r.champ.id: r for r in reponses}

        for champ_id, valeur_attendue in donnees_envoyees.items():
            if champ_id in reponses_dict:
                reponse = reponses_dict[champ_id]
                valeur_sauvegardee = None
                if reponse.valeur_texte:
                    valeur_sauvegardee = reponse.valeur_texte
                elif reponse.valeur_nombre is not None:
                    valeur_sauvegardee = reponse.valeur_nombre
                elif reponse.valeur_date is not None:
                    valeur_sauvegardee = str(reponse.valeur_date)
                elif reponse.valeur_bool is not None:
                    valeur_sauvegardee = reponse.valeur_bool

                if str(valeur_sauvegardee) == str(valeur_attendue):
                    print(f"   [OK] Champ {champ_id}: {valeur_attendue} OK")
                else:
                    print(f"   [ERROR] Champ {champ_id}: attendu '{valeur_attendue}', sauvegarde '{valeur_sauvegardee}' ERROR")
            else:
                print(f"   [ERROR] Champ {champ_id}: MANQUANT ERROR")

    except Exception as e:
        print(f"[ERROR] Erreur lors de la verification: {e}")
        import traceback
        traceback.print_exc()

def verifier_toutes_inscriptions():
    print(f"\n=== TOUTES LES INSCRIPTIONS ({Inscription.objects.count()}) ===\n")

    for inscription in Inscription.objects.all().order_by('-created_at')[:5]:
        reponses_count = inscription.reponses.count()
        print(f"ID {inscription.id}: {inscription.nom} {inscription.prenom} - {reponses_count} reponses - {inscription.created_at}")

if __name__ == '__main__':
    verifier_reponses()
    verifier_toutes_inscriptions()
