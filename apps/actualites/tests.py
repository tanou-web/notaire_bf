from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import ActualitesActualite

User = get_user_model()


class ActualiteAPITestCase(APITestCase):
    def setUp(self):
        # Créer un utilisateur admin et normal
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            nom='Admin',
            prenom='User'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123',
            nom='Normal',
            prenom='User'
        )
        
        # Créer des actualités de test
        self.actualite_publiee = ActualitesActualite.objects.create(
            titre='Actualité publiée',
            slug='actualite-publiee',
            contenu='Contenu de l\'actualité publiée',
            resume='Résumé de l\'actualité publiée',
            categorie='profession',
            auteur=self.admin_user,
            date_publication=timezone.now(),
            important=True,
            publie=True,
            vue=10,
            featured=False
        )
        
        self.actualite_non_publiee = ActualitesActualite.objects.create(
            titre='Actualité non publiée',
            slug='actualite-non-publiee',
            contenu='Contenu de l\'actualité non publiée',
            resume='Résumé de l\'actualité non publiée',
            categorie='juridique',
            auteur=self.admin_user,
            date_publication=timezone.now() + timezone.timedelta(days=1),  # Date future
            important=False,
            publie=False,
            vue=0,
            featured=False
        )
        
        # Token JWT pour l'admin
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        self.user_token = str(AccessToken.for_user(self.normal_user))
    
    def test_list_actualites_public(self):
        """Test d'accès public à la liste des actualités"""
        url = reverse('actualites:actualite-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier qu'on ne voit que les actualités publiées
        actualites = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(actualites), 1)  # Seulement l'actualité publiée
    
    def test_create_actualite_admin(self):
        """Test de création d'actualité par admin"""
        url = reverse('actualites:actualite-list')
        data = {
            'titre': 'Nouvelle actualité',
            'contenu': 'Contenu de la nouvelle actualité',
            'resume': 'Résumé de la nouvelle actualité',
            'categorie': 'formation',
            'important': False,
            'publie': True,
            'featured': False
        }
        
        # Sans authentification
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Avec authentification admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['titre'], 'Nouvelle actualité')
    
    def test_publiees_endpoint(self):
        """Test du endpoint des actualités publiées"""
        url = reverse('actualites:actualite-publiees')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier qu'on ne voit que les actualités publiées
        actualites = response.data['results'] if 'results' in response.data else response.data
        for actualite in actualites:
            self.assertTrue(actualite['publie'])
    
    def test_incrementer_vues(self):
        """Test d'incrémentation des vues"""
        url = reverse('actualites:actualite-incrementer-vues', args=[self.actualite_publiee.id])
        
        # Authentification requise pour cette action
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['vues'], 11)  # 10 initiales + 1
    
    def test_recherche_avancee(self):
        """Test de la recherche avancée"""
        url = reverse('actualites:actualite-recherche-avancee')
        response = self.client.get(f"{url}?q=publiée")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_par_categorie_endpoint(self):
        """Test du groupement par catégorie"""
        url = reverse('actualites:actualite-par-categorie')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Profession', response.data)


class ActualiteModelTestCase(TestCase):
    def test_est_publiee_property(self):
        """Test de la propriété est_publiee"""
        user = User.objects.create_user(username='test', password='test')
        actualite = ActualitesActualite.objects.create(
            titre='Test',
            slug='test',
            contenu='Contenu',
            categorie='profession',
            auteur=user,
            date_publication=timezone.now(),
            publie=True
        )
        
        self.assertTrue(actualite.est_publiee)
    
    def test_resume_auto_property(self):
        """Test de la propriété resume_auto"""
        actualite = ActualitesActualite.objects.create(
            titre='Test',
            slug='test',
            contenu='Un contenu très long qui dépasse les 150 caractères pour tester la génération automatique de résumé quand aucun résumé n\'est fourni par l\'utilisateur.',
            categorie='profession'
        )
        
        self.assertTrue(actualite.resume_auto.endswith('...'))
        self.assertLessEqual(len(actualite.resume_auto), 153)  # 150 + '...'