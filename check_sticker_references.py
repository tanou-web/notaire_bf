
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.ventes.models import VenteSticker, VenteStickerNotaire

ref = 'VNT-20260213-0A33BC' # From the user prompt details

print(f"Checking reference: {ref}")

vsn = VenteStickerNotaire.objects.filter(reference=ref).first()
if vsn:
    print(f"Found in VenteStickerNotaire: ID={vsn.id}, Notaire={vsn.notaire.nom_complet}")
else:
    print("Not found in VenteStickerNotaire")

vs = VenteSticker.objects.filter(reference=ref).first()
if vs:
    print(f"Found in VenteSticker: ID={vs.id}")
else:
    print("Not found in VenteSticker")

# Check if maybe it's VNT-20260213-A82BC0 (from the first part of the prompt)
ref2 = 'VNT-20260213-A82BC0'
print(f"\nChecking reference: {ref2}")
vsn2 = VenteStickerNotaire.objects.filter(reference=ref2).first()
if vsn2:
    print(f"Found in VenteStickerNotaire: ID={vsn2.id}, Notaire={vsn2.notaire.nom_complet}")
else:
    print("Not found in VenteStickerNotaire")
