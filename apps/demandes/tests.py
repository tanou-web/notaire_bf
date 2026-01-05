from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from .models import Demande, PieceJointe

User = get_user_model()


class DemandeModelTestCase(TestCase):
    """Tests pour le modèle Demande"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Dupont',
            prenom='Jean',
            password='testpass123'
        )

    def test_create_demande_authenticated(self):
        """Test de création d'une demande par un utilisateur authentifié"""
        demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_naissance',
            description='Demande d\'acte de naissance',
            urgence='normal'
        )

        self.assertEqual(demande.utilisateur, self.user)
        self.assertEqual(demande.type_demande, 'acte_naissance')
        self.assertEqual(demande.statut, 'attente_formulaire')
        self.assertIsNotNone(demande.numero_reference)

    def test_create_demande_anonymous(self):
        """Test de création d'une demande par un utilisateur anonyme"""
        demande = Demande.objects.create(
            email_contact='anonymous@example.com',
            telephone_contact='+22670123456',
            type_demande='acte_naissance',
            description='Demande anonyme',
            urgence='urgent'
        )

        self.assertIsNone(demande.utilisateur)
        self.assertEqual(demande.email_contact, 'anonymous@example.com')
        self.assertEqual(demande.telephone_contact, '+22670123456')
        self.assertEqual(demande.statut, 'attente_formulaire')

    def test_demande_str_representation(self):
        """Test de la représentation string d'une demande"""
        demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_mariage',
            description='Demande acte de mariage'
        )

        expected = f"Demande #{demande.numero_reference} - Dupont Jean"
        self.assertEqual(str(demande), expected)

    def test_demande_status_transitions(self):
        """Test des transitions de statut"""
        demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_naissance',
            description='Test statut'
        )

        # Test transitions valides
        valid_transitions = [
            ('attente_formulaire', 'en_cours'),
            ('en_cours', 'attente_paiement'),
            ('attente_paiement', 'paye'),
            ('paye', 'en_traitement'),
            ('en_traitement', 'finalise'),
        ]

        for old_status, new_status in valid_transitions:
            demande.statut = old_status
            demande.statut = new_status
            demande.save()
            demande.refresh_from_db()
            self.assertEqual(demande.statut, new_status)


class DemandeAPITestCase(APITestCase):
    """Tests pour l'API des demandes"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Dupont',
            prenom='Jean',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            nom='Admin',
            prenom='Super',
            password='admin123'
        )

    def test_create_demande_authenticated(self):
        """Test de création d'une demande par utilisateur authentifié"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            'type_demande': 'acte_naissance',
            'description': 'Demande acte de naissance pour dossier scolaire',
            'urgence': 'normal',
            'documents_requis': ['acte_mariage_parents', 'declaration_naissance']
        }

        url = reverse('demande-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type_demande'], 'acte_naissance')
        self.assertEqual(response.data['statut'], 'attente_formulaire')
        self.assertEqual(response.data['utilisateur']['id'], self.user.id)

    def test_create_demande_anonymous(self):
        """Test de création d'une demande par utilisateur anonyme"""
        data = {
            'email_contact': 'anonymous@example.com',
            'telephone_contact': '+22670123456',
            'nom_contact': 'Martin',
            'prenom_contact': 'Pierre',
            'type_demande': 'acte_mariage',
            'description': 'Demande acte de mariage',
            'urgence': 'urgent'
        }

        url = reverse('demande-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email_contact'], 'anonymous@example.com')
        self.assertIsNone(response.data['utilisateur'])

    def test_list_demandes_user(self):
        """Test de listage des demandes pour un utilisateur"""
        # Créer quelques demandes
        Demande.objects.create(utilisateur=self.user, type_demande='acte_naissance', description='Demande 1')
        Demande.objects.create(utilisateur=self.user, type_demande='acte_mariage', description='Demande 2')
        Demande.objects.create(email_contact='other@example.com', type_demande='acte_deces', description='Demande autre')

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('demande-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # L'utilisateur devrait voir ses 2 demandes
        self.assertEqual(len(response.data['results']), 2)

    def test_list_demandes_admin(self):
        """Test de listage de toutes les demandes pour l'admin"""
        # Créer des demandes
        Demande.objects.create(utilisateur=self.user, type_demande='acte_naissance', description='User demande')
        Demande.objects.create(email_contact='anon@example.com', type_demande='acte_mariage', description='Anonymous demande')

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('demande-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # L'admin devrait voir toutes les demandes
        self.assertEqual(len(response.data['results']), 2)

    def test_get_demande_detail(self):
        """Test de récupération du détail d'une demande"""
        demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_naissance',
            description='Demande détaillée'
        )

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('demande-detail', kwargs={'pk': demande.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Demande détaillée')
        self.assertEqual(response.data['numero_reference'], demande.numero_reference)

    def test_update_demande_status_admin(self):
        """Test de mise à jour du statut par l'admin"""
        demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_naissance',
            description='Test update'
        )

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {'statut': 'en_cours'}
        url = reverse('demande-detail', kwargs={'pk': demande.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        demande.refresh_from_db()
        self.assertEqual(demande.statut, 'en_cours')

    def test_user_cannot_update_status(self):
        """Test qu'un utilisateur normal ne peut pas changer le statut"""
        demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_naissance',
            description='Test'
        )

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {'statut': 'finalise'}
        url = reverse('demande-detail', kwargs={'pk': demande.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_demandes_by_status(self):
        """Test du filtrage des demandes par statut"""
        Demande.objects.create(utilisateur=self.user, type_demande='acte_naissance', statut='attente_formulaire')
        Demande.objects.create(utilisateur=self.user, type_demande='acte_mariage', statut='en_cours')

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('demande-list') + '?statut=en_cours'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['statut'], 'en_cours')

    def test_search_demandes(self):
        """Test de la recherche dans les demandes"""
        Demande.objects.create(utilisateur=self.user, type_demande='acte_naissance', description='Demande importante')
        Demande.objects.create(utilisateur=self.user, type_demande='acte_mariage', description='Demande urgente')

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('demande-list') + '?search=urgente'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('urgente', response.data['results'][0]['description'])


class PieceJointeTestCase(APITestCase):
    """Tests pour les pièces jointes"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Test',
            prenom='User',
            password='testpass123'
        )
        self.demande = Demande.objects.create(
            utilisateur=self.user,
            type_demande='acte_naissance',
            description='Demande avec pièces'
        )

    def test_upload_piece_jointe(self):
        """Test de téléversement d'une pièce jointe"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Simuler un fichier
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        file_content = b'Fichier test content'
        file = SimpleUploadedFile('test.pdf', file_content, content_type='application/pdf')

        data = {
            'demande': self.demande.pk,
            'nom_document': 'Acte de naissance',
            'type_document': 'acte_naissance',
            'fichier': file
        }

        url = reverse('piece-jointe-list')
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nom_document'], 'Acte de naissance')
        self.assertEqual(response.data['demande'], self.demande.pk)

        # Vérifier que le fichier a été créé en base
        piece = PieceJointe.objects.get(pk=response.data['id'])
        self.assertIsNotNone(piece.fichier)

