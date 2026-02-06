from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import PaiementsTransaction
from apps.demandes.models import DemandesDemande, DocumentsDocument

User = get_user_model()

class AnonymousPaymentTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123'
        )
        self.document = DocumentsDocument.objects.create(
            titre="Test Document", 
            description="Doc description",
            montant_base=1000
        )
        
        # Demande liée à un utilisateur
        self.demande_user = DemandesDemande.objects.create(
            utilisateur=self.user,
            document=self.document,
            montant_total=1000,
            statut='attente_paiement',
            reference='REF-USER-123'
        )
        
        # Demande anonyme (simulée avec utilisateur=None)
        self.demande_anon = DemandesDemande.objects.create(
            utilisateur=None,
            document=self.document,
            montant_total=1000,
            statut='attente_paiement',
            reference='REF-ANON-123',
            email_reception="anon@example.com"
        )
        
        self.url = reverse('paiements:initier-paiement')

    def test_anonymous_can_initiate_payment_with_id(self):
        """Test qu'un utilisateur anonyme peut initier un paiement avec l'ID valide"""
        data = {
            "demande_id": self.demande_anon.id,
            "type_paiement": "orange_money", 
            "telephone": "+22670000000"
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Erreur: {response.data}")
        
        # Vérifier qu'une transaction a été créée
        self.assertTrue(PaiementsTransaction.objects.filter(demande=self.demande_anon).exists())

    def test_anonymous_cannot_initiate_payment_for_wrong_status(self):
        """Test qu'on ne peut pas payer une demande qui n'est pas en attente de paiement"""
        self.demande_anon.statut = 'brouillon'
        self.demande_anon.save()
        
        data = {
            "demande_id": self.demande_anon.id,
            "type_paiement": "orange_money"
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_user_can_still_pay(self):
        """Test qu'un utilisateur authentifié peut toujours initier un paiement"""
        self.client.force_authenticate(user=self.user)
        data = {
            "demande_id": self.demande_user.id,
            "type_paiement": "moov_money"
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
