from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from django.contrib.auth import get_user_model
from .models import ContactInformations, ContactMessage
from datetime import datetime


class ContactAPITest(APITestCase):
    def setUp(self):
        # create a sample contact information
        now = datetime.now()
        ContactInformations.objects.create(type='email', valeur='contact@notairesbf.com', ordre=1, actif=True, created_at=now, updated_at=now)

    def test_get_contact_info(self):
        url = reverse('contact-info')
        client = APIClient()
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(isinstance(data, list))

    @patch('apps.communications.services.EmailService.send_contact_email')
    def test_post_contact_form_success(self, mock_send):
        mock_send.return_value = (True, 'sent')
        url = reverse('contact-form')
        client = APIClient()
        payload = {
            'name': 'Jean',
            'email': 'jean@example.com',
            'subject': 'Question',
            'message': 'Bonjour'
        }
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, 201)
        # saved in DB
        self.assertTrue(ContactMessage.objects.filter(email='jean@example.com').exists())

    @patch('apps.communications.services.EmailService.send_contact_email')
    def test_post_contact_form_failure(self, mock_send):
        mock_send.return_value = (False, 'smtp error')
        url = reverse('contact-form')
        client = APIClient()
        payload = {
            'name': 'Jean',
            'email': 'jean2@example.com',
            'subject': 'Question',
            'message': 'Bonjour'
        }
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, 500)
        # record still saved but marked as not sent
        obj = ContactMessage.objects.filter(email='jean2@example.com').first()
        self.assertIsNotNone(obj)
        self.assertFalse(obj.sent)