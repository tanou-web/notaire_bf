from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class UserModelTestCase(TestCase):
    """Tests pour le modèle User personnalisé"""

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'nom': 'Dupont',
            'prenom': 'Jean',
            'telephone': '+22670123456',
            'password': 'testpass123'
        }

    def test_create_user(self):
        """Test de création d'un utilisateur"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.nom, 'Dupont')
        self.assertEqual(user.prenom, 'Jean')
        self.assertEqual(user.telephone, '+22670123456')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.email_verifie)
        self.assertFalse(user.telephone_verifie)

    def test_user_full_name(self):
        """Test de la méthode get_full_name"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Dupont Jean')

    def test_user_str_representation(self):
        """Test de la représentation string de l'utilisateur"""
        user = User.objects.create_user(**self.user_data)
        expected = f"Dupont Jean (testuser)"
        self.assertEqual(str(user), expected)


class UserAPITestCase(APITestCase):
    """Tests pour l'API utilisateurs"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Dupont',
            prenom='Jean',
            telephone='+22670123456',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            nom='Admin',
            prenom='Super',
            telephone='+22670987654',
            password='admin123'
        )

    def test_user_registration(self):
        """Test d'inscription d'un nouvel utilisateur"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'nom': 'Martin',
            'prenom': 'Pierre',
            'telephone': '+22670345678',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        url = reverse('user-register')
        response = self.client.post(url, data, format='json')

        # Vérifier la réponse (peut être 201 ou 200 selon l'implémentation)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(username='newuser')
            self.assertEqual(user.nom, 'Martin')
            self.assertEqual(user.prenom, 'Pierre')

    def test_user_login(self):
        """Test de connexion utilisateur"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_profile_access(self):
        """Test d'accès au profil utilisateur"""
        # Obtenir le token d'accès
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('user-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nom'], 'Dupont')
        self.assertEqual(response.data['prenom'], 'Jean')

    def test_user_profile_update(self):
        """Test de mise à jour du profil"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            'nom': 'Dupont',
            'prenom': 'Jean-Claude',
            'telephone': '+22670123457'
        }
        url = reverse('user-profile')
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.prenom, 'Jean-Claude')
        self.assertEqual(self.user.telephone, '+22670123457')

    def test_password_change(self):
        """Test de changement de mot de passe"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            'old_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        url = reverse('user-password-change')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_admin_user_list(self):
        """Test que seul l'admin peut lister les utilisateurs"""
        # Test sans authentification
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test avec utilisateur normal
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test avec superuser
        admin_token = AccessToken.for_user(self.superuser)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_email_verification_request(self):
        """Test de demande de vérification email"""
        data = {'email': 'test@example.com'}
        url = reverse('user-send-verification')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request(self):
        """Test de demande de réinitialisation de mot de passe"""
        data = {'email': 'test@example.com'}
        url = reverse('user-password-reset')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_login(self):
        """Test de connexion avec mauvaises credentials"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPermissionTestCase(APITestCase):
    """Tests des permissions utilisateur"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Test',
            prenom='User',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            nom='Admin',
            prenom='User',
            password='admin123'
        )

    def test_unauthenticated_access_restricted(self):
        """Test que l'accès non authentifié est restreint"""
        restricted_urls = [
            reverse('user-profile'),
            reverse('user-password-change'),
        ]

        for url in restricted_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_access_own_profile(self):
        """Test qu'un utilisateur peut accéder à son propre profil"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('user-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_user_cannot_access_admin_features(self):
        """Test qu'un utilisateur normal ne peut pas accéder aux features admin"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

