# tests_nouveaux.py - Tests pour ContactInformations avec lat/lng
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ContactInformations


class ContactInformationsGeolocTestCase(TestCase):
    """Tests pour ContactInformations avec géolocalisation"""
    
    def setUp(self):
        self.contact_adresse = ContactInformations.objects.create(
            type='adresse',
            valeur='123 Avenue de la Nation, Ouagadougou',
            latitude=12.3714,
            longitude=-1.5197,
            ordre=1,
            actif=True
        )
    
    def test_geolocalisation_fields(self):
        """Test que les champs latitude/longitude sont présents"""
        self.assertIsNotNone(self.contact_adresse.latitude)
        self.assertIsNotNone(self.contact_adresse.longitude)
        self.assertEqual(float(self.contact_adresse.latitude), 12.3714)
        self.assertEqual(float(self.contact_adresse.longitude), -1.5197)
    
    def test_contact_without_geoloc(self):
        """Test que les coordonnées sont optionnelles"""
        contact_tel = ContactInformations.objects.create(
            type='telephone',
            valeur='+226 25 30 60 70',
            ordre=2,
            actif=True
        )
        self.assertIsNone(contact_tel.latitude)
        self.assertIsNone(contact_tel.longitude)

