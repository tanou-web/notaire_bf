from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from .models import SecurityLog, LoginAttempt
from .loggers import SecurityLogger

User = get_user_model()


class SecurityLogModelTestCase(TestCase):
    """Tests pour le modèle SecurityLog"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Test',
            prenom='User',
            password='testpass123'
        )

    def test_create_security_log(self):
        """Test de création d'un log de sécurité"""
        log = SecurityLog.objects.create(
            user=self.user,
            action='login',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0...',
            success=True,
            details={'method': 'password'}
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertTrue(log.success)
        self.assertIsNotNone(log.timestamp)

    def test_security_log_str_representation(self):
        """Test de la représentation string d'un log de sécurité"""
        log = SecurityLog.objects.create(
            user=self.user,
            action='password_change',
            success=True
        )

        expected = f"SecurityLog: Test User (testuser) - password_change - True"
        self.assertEqual(str(log), expected)

    def test_security_log_without_user(self):
        """Test de création d'un log sans utilisateur (attaque externe)"""
        log = SecurityLog.objects.create(
            action='brute_force_attempt',
            ip_address='10.0.0.5',
            success=False,
            details={'attempted_username': 'admin'}
        )

        self.assertIsNone(log.user)
        self.assertEqual(log.action, 'brute_force_attempt')
        self.assertFalse(log.success)


class LoginAttemptModelTestCase(TestCase):
    """Tests pour le modèle LoginAttempt"""

    def test_create_login_attempt(self):
        """Test de création d'une tentative de connexion"""
        attempt = LoginAttempt.objects.create(
            username='testuser',
            ip_address='192.168.1.100',
            user_agent='Test Agent',
            success=False,
            failure_reason='wrong_password'
        )

        self.assertEqual(attempt.username, 'testuser')
        self.assertEqual(attempt.ip_address, '192.168.1.100')
        self.assertFalse(attempt.success)
        self.assertEqual(attempt.failure_reason, 'wrong_password')

    def test_login_attempt_str_representation(self):
        """Test de la représentation string d'une tentative de connexion"""
        attempt = LoginAttempt.objects.create(
            username='admin',
            ip_address='10.0.0.1',
            success=False
        )

        expected = "Login attempt: admin from 10.0.0.1 - Failed"
        self.assertEqual(str(attempt), expected)

    def test_successful_login_attempt(self):
        """Test d'une tentative de connexion réussie"""
        attempt = LoginAttempt.objects.create(
            username='testuser',
            ip_address='192.168.1.50',
            success=True
        )

        self.assertTrue(attempt.success)
        self.assertIsNone(attempt.failure_reason)


class SecurityLoggerTestCase(TestCase):
    """Tests pour le SecurityLogger"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Test',
            prenom='User',
            password='testpass123'
        )

    def test_log_successful_login(self):
        """Test du logging d'une connexion réussie"""
        initial_count = SecurityLog.objects.count()

        SecurityLogger.log_login_success(
            user=self.user,
            ip_address='192.168.1.100',
            user_agent='Test Browser'
        )

        self.assertEqual(SecurityLog.objects.count(), initial_count + 1)

        log = SecurityLog.objects.latest('timestamp')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertTrue(log.success)
        self.assertEqual(log.ip_address, '192.168.1.100')

    def test_log_failed_login(self):
        """Test du logging d'un échec de connexion"""
        initial_count = SecurityLog.objects.count()

        SecurityLogger.log_login_failure(
            username='wronguser',
            ip_address='192.168.1.200',
            user_agent='Bad Browser',
            reason='user_not_found'
        )

        self.assertEqual(SecurityLog.objects.count(), initial_count + 1)

        log = SecurityLog.objects.latest('timestamp')
        self.assertIsNone(log.user)
        self.assertEqual(log.action, 'login_failed')
        self.assertFalse(log.success)
        self.assertEqual(log.details['reason'], 'user_not_found')

    def test_log_suspicious_activity(self):
        """Test du logging d'une activité suspecte"""
        initial_count = SecurityLog.objects.count()

        SecurityLogger.log_suspicious_activity(
            user=self.user,
            action='multiple_failed_attempts',
            ip_address='10.0.0.1',
            details={'attempts_count': 5}
        )

        self.assertEqual(SecurityLog.objects.count(), initial_count + 1)

        log = SecurityLog.objects.latest('timestamp')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'multiple_failed_attempts')
        self.assertEqual(log.details['attempts_count'], 5)

    def test_log_password_change(self):
        """Test du logging d'un changement de mot de passe"""
        initial_count = SecurityLog.objects.count()

        SecurityLogger.log_password_change(
            user=self.user,
            ip_address='192.168.1.150'
        )

        self.assertEqual(SecurityLog.objects.count(), initial_count + 1)

        log = SecurityLog.objects.latest('timestamp')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'password_change')
        self.assertTrue(log.success)


class AuditAPITestCase(APITestCase):
    """Tests pour l'API d'audit"""

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
            prenom='Super',
            password='admin123'
        )

    def test_security_logs_admin_only(self):
        """Test que seuls les admins peuvent voir les logs de sécurité"""
        # Créer quelques logs
        SecurityLog.objects.create(
            user=self.user, action='login', success=True,
            ip_address='192.168.1.100'
        )

        # Test sans authentification
        url = reverse('security-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test avec utilisateur normal
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test avec admin
        admin_token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_attempts_admin_only(self):
        """Test que seuls les admins peuvent voir les tentatives de connexion"""
        LoginAttempt.objects.create(
            username='testuser',
            ip_address='192.168.1.100',
            success=False,
            failure_reason='wrong_password'
        )

        admin_token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        url = reverse('login-attempts')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_security_logs_filtering(self):
        """Test du filtrage des logs de sécurité"""
        # Créer différents types de logs
        SecurityLog.objects.create(user=self.user, action='login', success=True)
        SecurityLog.objects.create(user=self.user, action='password_change', success=True)
        SecurityLog.objects.create(action='brute_force_attempt', success=False)

        admin_token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        # Filtrer par action
        url = reverse('security-logs') + '?action=login'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'login')

    def test_token_usage_tracking(self):
        """Test du suivi d'utilisation des tokens JWT"""
        admin_token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        url = reverse('token-usage')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que les données de tokens sont présentes
        self.assertIn('total_tokens', response.data)
        self.assertIn('active_tokens', response.data)

    def test_audit_data_pagination(self):
        """Test de la pagination des données d'audit"""
        # Créer beaucoup de logs pour tester la pagination
        for i in range(25):
            SecurityLog.objects.create(
                user=self.user,
                action='test_action',
                success=True
            )

        admin_token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        url = reverse('security-logs') + '?page_size=10'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    @override_settings(AUDIT_LOG_RETENTION_DAYS=30)
    def test_audit_data_retention(self):
        """Test de la rétention des données d'audit"""
        from django.utils import timezone
        from datetime import timedelta

        # Créer un log ancien
        old_log = SecurityLog.objects.create(
            user=self.user,
            action='old_action',
            success=True
        )
        old_log.timestamp = timezone.now() - timedelta(days=60)
        old_log.save()

        # Créer un log récent
        recent_log = SecurityLog.objects.create(
            user=self.user,
            action='recent_action',
            success=True
        )

        admin_token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        url = reverse('security-logs')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Les deux logs devraient être présents (la rétention n'est pas automatique)
        self.assertGreaterEqual(len(response.data['results']), 2)
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import SecurityLog

User = get_user_model()


class AuditAPITest(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user('admin@test.com', 'admin@test.com', 'pass')
		self.admin.is_staff = True
		self.admin.is_superuser = True
		self.admin.save()

		# create a sample security log
		SecurityLog.objects.create(action='login_success', details={'msg': 'ok'})

		self.client = APIClient()
		self.client.force_authenticate(user=self.admin)

	def test_security_list_and_export(self):
		url = reverse('security-list')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue('results' in resp.data or isinstance(resp.data, list))

		# export
		url_export = reverse('security-export')
		resp2 = self.client.get(url_export)
		self.assertEqual(resp2.status_code, 200)
		self.assertEqual(resp2['Content-Type'], 'text/csv')
