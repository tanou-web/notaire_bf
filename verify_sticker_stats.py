
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

def verify_stats_logic():
    print("Initialising Django...")
    try:
        django.setup()
        print("Django setup successful")
    except Exception as e:
        print(f"Django setup failed: {e}")
        return

    from apps.ventes.models import VenteSticker, VenteStickerNotaire, DemandeVente
    from django.db.models import Q, Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    print("Testing Query Logic...")
    
    nom_sticker = "Sticker" # Example filter
    date_debut = timezone.now() - timedelta(days=30)
    
    filtres_ventes = Q(date_vente__gte=date_debut)
    filtres_ventes_notaires = Q(date_vente__gte=date_debut)

    if nom_sticker:
        filtres_ventes &= Q(sticker__nom__icontains=nom_sticker)
        filtres_ventes_notaires &= Q(type_sticker__nom__icontains=nom_sticker)

    print(f"Filter VenteSticker: {filtres_ventes}")
    print(f"Filter VenteStickerNotaire: {filtres_ventes_notaires}")

    try:
        # We don't necessarily need data to check if the query is valid SQL-wise
        # but we can try to get the SQL string
        vs_qs = VenteSticker.objects.filter(filtres_ventes)
        vns_qs = VenteStickerNotaire.objects.filter(filtres_ventes_notaires)
        
        print("Querysets created successfully")
        
        # Check aggregation
        ventes_clients = vs_qs.aggregate(
            total_stickers=Sum('quantite'),
            total_ventes=Count('id'),
            revenu_total=Sum('montant_total')
        )
        print(f"VenteSticker aggregation test: {ventes_clients}")

        ventes_notaires_stock = vns_qs.aggregate(
            total_stickers=Sum('quantite'),
            total_ventes=Count('id'),
            revenu_total=Sum('montant_total')
        )
        print(f"VenteStickerNotaire aggregation test: {ventes_notaires_stock}")

    except Exception as e:
        print(f"Query logic failed: {e}")

if __name__ == "__main__":
    verify_stats_logic()
