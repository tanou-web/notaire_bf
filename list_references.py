
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.ventes.models import VenteSticker, VenteStickerNotaire

print("--- VenteStickerNotaire (VNT-...) ---")
for v in VenteStickerNotaire.objects.all()[:10]:
    print(f"Ref: {v.reference}, ID: {v.id}")

print("\n--- VenteSticker (VEN-...) ---")
for v in VenteSticker.objects.all()[:10]:
    print(f"Ref: {v.reference}, ID: {v.id}")
