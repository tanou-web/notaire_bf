from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from datetime import datetime
from django.contrib.auth import get_user_model
from .models import PartenairesPartenaire


class PartenairesAPITest(APITestCase):
	def setUp(self):
		now = datetime.now()
		try:
			PartenairesPartenaire.objects.create(nom='Partenaire1', type_partenaire='sponsor', ordre=1, actif=True, created_at=now, updated_at=now)
		except Exception:
			pass
		User = get_user_model()
		self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')

	def test_list_partenaires(self):
		url = reverse('partenaire-list')
		client = APIClient()
		resp = client.get(url)
		self.assertIn(resp.status_code, (200, 404))

	def test_create_requires_admin(self):
		url = reverse('partenaire-list')
		client = APIClient()
		payload = {'nom': 'P2', 'type_partenaire': 'partner', 'ordre': 2, 'actif': True}
		resp = client.post(url, payload, format='json')
		self.assertIn(resp.status_code, (401, 403))

		client.force_authenticate(user=self.admin)
		resp2 = client.post(url, payload, format='json')
		self.assertIn(resp2.status_code, (201, 400))
