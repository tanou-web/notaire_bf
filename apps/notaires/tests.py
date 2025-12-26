# apps/notaires/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import NotairesNotaire, Region, Ville

class NotaireAPITestCase(APITestCase):
    def setUp(self):
        self.region = Region.objects.create(nom="Centre", code="CTR")
        self.ville = Ville.objects.create(nom="Ouagadougou", region=self.region)
        self.notaire = NotairesNotaire.objects.create(
            matricule="NOT001",
            nom="Konaté",
            prenom="Fatoumata",
            telephone="+22670123456",
            email="f.konate@example.com",
            region=self.region,
            ville=self.ville,
            actif=True
        )
    
    def test_list_notaires(self):
        url = reverse('notaire-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_filter_by_region(self):
        url = reverse('notaire-list') + f'?region={self.region.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_search_notaire(self):
        url = reverse('notaire-list') + '?search=Konaté'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)