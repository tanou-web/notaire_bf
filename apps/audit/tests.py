from django.test import TestCase
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
