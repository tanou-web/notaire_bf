import os
import django
import json
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

client = Client()
from apps.demandes.models import DemandesDemande
from apps.documents.models import DocumentsDocument

# Create a document if none exists
doc = DocumentsDocument.objects.first()
if not doc:
    from apps.organisation.models import OrganisationService
    srv = OrganisationService.objects.create(nom="Test Service")
    doc = DocumentsDocument.objects.create(nom="Test Doc", service=srv, prix=1000)

# Create an anonymous demande
REF = "DEM-TEST-VISIBILITY-123"
DemandesDemande.objects.filter(reference=REF).delete()
d = DemandesDemande.objects.create(
    reference=REF,
    document=doc,
    email_reception="test@tracking.com",
    utilisateur=None,
    statut="attente_paiement"
)

print(f"Created Demande {d.id} with REF {REF}")

# Test 1: Search by reference param
url1 = f"/api/demandes/demandes/?reference={REF}"
print(f"GET {url1}")
res1 = client.get(url1)
print(f"Status: {res1.status_code}, Count: {len(res1.json().get('results', []))}")

# Test 2: Search by q param
url2 = f"/api/demandes/demandes/?q={REF}"
print(f"GET {url2}")
res2 = client.get(url2)
print(f"Status: {res2.status_code}, Count: {len(res2.json().get('results', []))}")

# Test 3: Fetch by ID with reference param (Tracking detail)
url3 = f"/api/demandes/demandes/{d.id}/?reference={REF}"
print(f"GET {url3}")
res3 = client.get(url3)
print(f"Status: {res3.status_code}")

# Test 4: Fetch by ID WITHOUT reference param (Should fail for anonymous)
url4 = f"/api/demandes/demandes/{d.id}/"
print(f"GET {url4}")
res4 = client.get(url4)
print(f"Status: {res4.status_code} (Expected 404 or 403)")
