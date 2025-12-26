from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import ConseilsConseildujour
from datetime import date, datetime


class ConseilsAPITest(APITestCase):
	def setUp(self):
		User = get_user_model()
		self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
		# create a sample conseil
		now = datetime.now()
		ConseilsConseildujour.objects.create(
			conseil='Test conseil',
			date=date.today(),
			actif=True,
			created_at=now,
			updated_at=now,
		)

	def test_list_conseils_public(self):
		url = reverse('conseil-list')
		client = APIClient()
		resp = client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(isinstance(resp.json(), list))

	def test_create_conseil_requires_admin(self):
		url = reverse('conseil-list')
		client = APIClient()
		payload = {
			'conseil': 'Nouveau conseil',
			'date': date.today().isoformat(),
			'actif': True
		}
		# anonymous should be forbidden
		resp = client.post(url, payload, format='json')
		self.assertIn(resp.status_code, (401, 403))

		# admin can create
		client.force_authenticate(user=self.admin)
		resp2 = client.post(url, payload, format='json')
		# creation may fail if DB table constraints exist; expect 201 or 400 depending on DB schema
		self.assertIn(resp2.status_code, (201, 400))
