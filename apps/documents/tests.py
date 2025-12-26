from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User
from .models import DocumentsDocument, DocumentsTextelegal


class DocumentAPITestCase(APITestCase):
    def setUp(self):
        # Créer un utilisateur admin et normal
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123'
        )
        
        # Créer des données de test
        self.document = DocumentsDocument.objects.create(
            reference='DOC-001',
            nom='Acte de vente',
            description='Document pour acte de vente',
            prix=50000,
            delai_heures=48,
            actif=True
        )
        
        self.document_inactif = DocumentsDocument.objects.create(
            reference='DOC-002',
            nom='Test Inactif',
            description='Document inactif',
            prix=30000,
            delai_heures=72,
            actif=False
        )
        
        # Token JWT pour l'admin
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        
    def test_list_documents_public(self):
        """Test d'accès public à la liste des documents"""
        url = reverse('documents:document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier qu'on ne voit que les documents actifs (pour les non-authentifiés)
        documents = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len([d for d in documents if d['actif']]), 1)
    
    def test_create_document_admin(self):
        """Test de création de document par admin"""
        url = reverse('documents:document-list')
        data = {
            'reference': 'DOC-003',
            'nom': 'Nouveau document',
            'description': 'Description du nouveau document',
            'prix': 75000,
            'delai_heures': 48,
            'actif': True
        }
        
        # Sans authentification
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Avec authentification admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reference'], 'DOC-003')
    
    def test_stats_endpoint(self):
        """Test du endpoint de statistiques"""
        url = reverse('documents:document-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_documents', response.data)
        self.assertIn('documents_actifs', response.data)
        self.assertIn('prix_moyen', response.data)
    
    def test_actifs_endpoint(self):
        """Test du endpoint des documents actifs"""
        url = reverse('documents:document-actifs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier qu'on ne voit que les documents actifs
        documents = response.data['results'] if 'results' in response.data else response.data
        for doc in documents:
            self.assertTrue(doc['actif'])


class TexteLegalAPITestCase(APITestCase):
    def setUp(self):
        self.texte = DocumentsTextelegal.objects.create(
            type_texte='loi',
            titre='Loi sur les notaires',
            fichier='/uploads/textes/loi_notaires.pdf',
            ordre=1
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
        self.admin_token = str(AccessToken.for_user(self.admin_user))
    
    def test_list_textes_legaux(self):
        url = reverse('documents:textelegal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_types_endpoint(self):
        url = reverse('documents:textelegal-types')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_par_type_endpoint(self):
        url = reverse('documents:textelegal-par-type')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)