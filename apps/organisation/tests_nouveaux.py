# tests_nouveaux.py - Tests pour les nouveaux modèles Organisation
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import (
    OrganisationMembrebureau,
    OrganisationHistorique,
    OrganisationMission
)
from datetime import date

User = get_user_model()


class OrganisationHistoriqueTestCase(TestCase):
    """Tests pour le modèle OrganisationHistorique"""
    
    def setUp(self):
        self.historique = OrganisationHistorique.objects.create(
            titre="Création de l'Ordre",
            contenu="L'Ordre des Notaires a été créé en 1960...",
            date_evenement=date(1960, 1, 1),
            ordre=1,
            actif=True
        )
    
    def test_historique_creation(self):
        """Test de création d'un événement historique"""
        self.assertEqual(str(self.historique), "Création de l'Ordre (1960-01-01)")
        self.assertTrue(self.historique.actif)
    
    def test_historique_ordering(self):
        """Test de l'ordre d'affichage"""
        h2 = OrganisationHistorique.objects.create(
            titre="Réforme de 1990",
            contenu="Réforme importante...",
            date_evenement=date(1990, 1, 1),
            ordre=2,
            actif=True
        )
        historiques = OrganisationHistorique.objects.filter(actif=True)
        self.assertEqual(historiques.first(), self.historique)  # ordre=1 vient en premier


class OrganisationMissionTestCase(TestCase):
    """Tests pour le modèle OrganisationMission"""
    
    def setUp(self):
        self.mission = OrganisationMission.objects.create(
            titre="Protection de la profession",
            description="Protéger les intérêts de la profession notariale",
            icone="shield",
            ordre=1,
            actif=True
        )
    
    def test_mission_creation(self):
        """Test de création d'une mission"""
        self.assertEqual(str(self.mission), "Protection de la profession")
        self.assertTrue(self.mission.actif)
        self.assertEqual(self.mission.icone, "shield")


class OrganisationMembrebureauMotPresidentTestCase(TestCase):
    """Tests pour le champ mot_du_president"""
    
    def setUp(self):
        self.president = OrganisationMembrebureau.objects.create(
            nom="Kaboré",
            prenom="Ali",
            poste="president",
            mot_du_president="Message important du Président de l'Ordre...",
            ordre=1,
            actif=True
        )
    
    def test_mot_du_president(self):
        """Test que le mot du président est enregistré"""
        self.assertIsNotNone(self.president.mot_du_president)
        self.assertIn("Président", self.president.mot_du_president)


class OrganisationAPIHistoriqueTestCase(APITestCase):
    """Tests API pour l'historique"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='test123',
            nom='Admin',
            prenom='User'
        )
        self.historique = OrganisationHistorique.objects.create(
            titre="Événement historique",
            contenu="Contenu test",
            ordre=1,
            actif=True
        )
    
    def test_list_historique_public(self):
        """Test accès public à la liste de l'historique"""
        url = reverse('historique-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_historique_requires_admin(self):
        """Test que la création nécessite un admin"""
        url = reverse('historique-list')
        data = {
            'titre': 'Nouvel événement',
            'contenu': 'Contenu',
            'ordre': 2,
            'actif': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Avec authentification admin
        token = str(AccessToken.for_user(self.admin))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])


class OrganisationAPIMissionTestCase(APITestCase):
    """Tests API pour les missions"""
    
    def setUp(self):
        self.client = APIClient()
        self.mission = OrganisationMission.objects.create(
            titre="Mission test",
            description="Description test",
            icone="test",
            ordre=1,
            actif=True
        )
    
    def test_list_missions_public(self):
        """Test accès public à la liste des missions"""
        url = reverse('mission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

