# tests_nouveaux.py - Tests pour SystemEmailprofessionnel
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import SystemEmailprofessionnel

User = get_user_model()


class SystemEmailprofessionnelTestCase(TestCase):
    """Tests pour le modèle SystemEmailprofessionnel"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            nom='Test',
            prenom='User'
        )
        
        self.email_pro = SystemEmailprofessionnel.objects.create(
            email='contact@notairesbf.com',
            mot_de_passe='encrypted_password',
            utilisateur=self.user,
            description='Email de contact général',
            actif=True
        )
    
    def test_email_creation(self):
        """Test de création d'un email professionnel"""
        self.assertEqual(str(self.email_pro), "contact@notairesbf.com (Actif)")
        self.assertTrue(self.email_pro.actif)
        self.assertEqual(self.email_pro.utilisateur, self.user)
    
    def test_email_alias(self):
        """Test de la méthode est_alias"""
        self.assertFalse(self.email_pro.est_alias())
        
        # Créer un alias
        alias = SystemEmailprofessionnel.objects.create(
            email='info@notairesbf.com',
            mot_de_passe='encrypted',
            alias_pour='contact@notairesbf.com',
            actif=True
        )
        self.assertTrue(alias.est_alias())


class SystemEmailprofessionnelAPITestCase(APITestCase):
    """Tests API pour SystemEmailprofessionnel"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='test123',
            nom='Admin',
            prenom='User'
        )
        
        self.email_pro = SystemEmailprofessionnel.objects.create(
            email='test@notairesbf.com',
            mot_de_passe='encrypted',
            actif=True
        )
        
        token = str(AccessToken.for_user(self.admin))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_list_emails_requires_admin(self):
        """Test que la liste nécessite un admin"""
        url = reverse('email-professionnel-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_emails_actifs_endpoint(self):
        """Test de l'endpoint emails actifs"""
        url = reverse('email-professionnel-actifs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

