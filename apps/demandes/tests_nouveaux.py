# tests_nouveaux.py - Tests pour DemandesPieceJointe
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import DemandesDemande, DemandesPieceJointe
from apps.documents.models import DocumentsDocument
from apps.utilisateurs.models import UtilisateursUser

User = get_user_model()


class DemandesPieceJointeTestCase(TestCase):
    """Tests pour le modèle DemandesPieceJointe"""
    
    def setUp(self):
        # Créer un utilisateur de test
        self.user = UtilisateursUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            nom='Test',
            prenom='User',
            telephone='+22670123456',
            email_verifie=True
        )
        
        # Créer un document de test
        self.document = DocumentsDocument.objects.create(
            reference='DOC-TEST',
            nom='Document test',
            description='Test',
            prix=10000,
            delai_heures=48,
            actif=True
        )
        
        # Créer une demande de test
        self.demande = DemandesDemande.objects.create(
            reference='DEM-TEST-001',
            utilisateur=self.user,
            document=self.document,
            statut='attente_formulaire',
            montant_total=10000
        )
    
    def test_piece_jointe_creation(self):
        """Test de création d'une pièce jointe"""
        fichier = SimpleUploadedFile(
            "test_cnib.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        piece = DemandesPieceJointe.objects.create(
            demande=self.demande,
            type_piece='cnib',
            fichier=fichier,
            description='CNIB de test'
        )
        
        self.assertEqual(piece.demande, self.demande)
        self.assertEqual(piece.type_piece, 'cnib')
        self.assertIsNotNone(piece.nom_original)
        self.assertIsNotNone(piece.taille_fichier)
    
    def test_taille_formatee(self):
        """Test du formatage de la taille"""
        fichier = SimpleUploadedFile("test.pdf", b"x" * 1024, content_type="application/pdf")
        piece = DemandesPieceJointe.objects.create(
            demande=self.demande,
            type_piece='cnib',
            fichier=fichier
        )
        self.assertIn("KB", piece.taille_formatee)


class DemandesPieceJointeAPITestCase(APITestCase):
    """Tests API pour les pièces jointes"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            nom='Test',
            prenom='User',
            telephone='+22670123456'
        )
        
        # Créer demande
        self.document = DocumentsDocument.objects.create(
            reference='DOC-TEST',
            nom='Document test',
            description='Test',
            prix=10000,
            delai_heures=48,
            actif=True
        )
        
        self.demande = DemandesDemande.objects.create(
            reference='DEM-TEST-001',
            utilisateur=self.user,
            document=self.document,
            statut='attente_formulaire',
            montant_total=10000
        )
        
        token = str(AccessToken.for_user(self.user))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_list_pieces_jointes(self):
        """Test de liste des pièces jointes"""
        url = reverse('piecejointe-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

