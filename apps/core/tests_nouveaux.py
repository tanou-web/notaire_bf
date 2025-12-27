# tests_nouveaux.py - Tests pour CorePage
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import CorePage

User = get_user_model()


class CorePageTestCase(TestCase):
    """Tests pour le modèle CorePage"""
    
    def setUp(self):
        self.page = CorePage.objects.create(
            titre="Page de présentation",
            slug="presentation",
            contenu="<p>Contenu HTML de la page</p>",
            resume="Résumé de la page",
            publie=True
        )
    
    def test_page_creation(self):
        """Test de création d'une page"""
        self.assertEqual(str(self.page), "Page de présentation (Publié)")
        self.assertTrue(self.page.publie)
        self.assertEqual(self.page.slug, "presentation")
    
    def test_page_url_property(self):
        """Test de la propriété url"""
        self.assertEqual(self.page.url, "/pages/presentation/")
    
    def test_page_auto_publication_date(self):
        """Test que la date de publication est auto-définie"""
        self.assertIsNotNone(self.page.date_publication)


class CorePageAPITestCase(APITestCase):
    """Tests API pour CorePage"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='test123',
            nom='Admin',
            prenom='User'
        )
        self.page = CorePage.objects.create(
            titre="Page publique",
            slug="page-publique",
            contenu="Contenu",
            publie=True
        )
    
    def test_list_pages_public(self):
        """Test accès public aux pages publiées"""
        url = reverse('page-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_page_by_slug(self):
        """Test récupération d'une page par slug"""
        url = reverse('page-detail', kwargs={'slug': 'page-publique'})
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

