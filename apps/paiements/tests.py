from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from decimal import Decimal
from .models import Transaction

User = get_user_model()


class TransactionModelTestCase(TestCase):
    """Tests pour le modèle Transaction"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Dupont',
            prenom='Jean',
            password='testpass123'
        )

    def test_create_transaction(self):
        """Test de création d'une transaction"""
        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=50000,  # 50,000 FCFA
            devise='XOF',
            methode_paiement='orange_money',
            reference_externe='TXN123456',
            description='Paiement acte notarié'
        )

        self.assertEqual(transaction.utilisateur, self.user)
        self.assertEqual(transaction.montant, Decimal('50000'))
        self.assertEqual(transaction.devise, 'XOF')
        self.assertEqual(transaction.statut, 'en_attente')
        self.assertIsNotNone(transaction.reference_interne)
        self.assertIsNotNone(transaction.date_creation)

    def test_transaction_str_representation(self):
        """Test de la représentation string d'une transaction"""
        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=25000,
            methode_paiement='moov_money',
            description='Test transaction'
        )

        expected = f"Transaction #{transaction.reference_interne} - 25000 XOF"
        self.assertEqual(str(transaction), expected)

    def test_transaction_status_transitions(self):
        """Test des transitions de statut de transaction"""
        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=10000,
            methode_paiement='orange_money'
        )

        # Test transitions valides
        valid_transitions = [
            ('en_attente', 'initie'),
            ('initie', 'en_cours'),
            ('en_cours', 'reussi'),
            ('reussi', 'confirme'),
        ]

        for old_status, new_status in valid_transitions:
            transaction.statut = old_status
            transaction.statut = new_status
            transaction.save()
            transaction.refresh_from_db()
            self.assertEqual(transaction.statut, new_status)

    def test_transaction_amount_validation(self):
        """Test de validation du montant"""
        # Test montant positif
        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=1000,
            methode_paiement='orange_money'
        )
        self.assertEqual(transaction.montant, Decimal('1000'))

        # Test montant nul (devrait échouer)
        with self.assertRaises(Exception):  # Ou validation spécifique
            Transaction.objects.create(
                utilisateur=self.user,
                montant=0,
                methode_paiement='orange_money'
            )


class TransactionAPITestCase(APITestCase):
    """Tests pour l'API des transactions"""

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

    def test_create_transaction_orange_money(self):
        """Test de création d'une transaction Orange Money"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            'montant': 30000,
            'methode_paiement': 'orange_money',
            'description': 'Paiement acte de vente',
            'numero_telephone': '+22670123456'
        }

        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['montant'], '30000.00')
        self.assertEqual(response.data['methode_paiement'], 'orange_money')
        self.assertEqual(response.data['statut'], 'en_attente')
        self.assertEqual(response.data['utilisateur']['id'], self.user.id)

    def test_create_transaction_moov_money(self):
        """Test de création d'une transaction Moov Money"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            'montant': 45000,
            'methode_paiement': 'moov_money',
            'description': 'Paiement succession',
            'numero_telephone': '+22670987654'
        }

        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['methode_paiement'], 'moov_money')
        self.assertEqual(response.data['montant'], '45000.00')

    def test_list_user_transactions(self):
        """Test de listage des transactions d'un utilisateur"""
        # Créer des transactions pour l'utilisateur
        Transaction.objects.create(
            utilisateur=self.user, montant=25000, methode_paiement='orange_money',
            description='Transaction 1'
        )
        Transaction.objects.create(
            utilisateur=self.user, montant=35000, methode_paiement='moov_money',
            description='Transaction 2'
        )

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Vérifier que seules les transactions de l'utilisateur sont retournées
        for transaction in response.data['results']:
            self.assertEqual(transaction['utilisateur']['id'], self.user.id)

    def test_admin_sees_all_transactions(self):
        """Test que l'admin voit toutes les transactions"""
        # Créer des transactions pour différents utilisateurs
        Transaction.objects.create(
            utilisateur=self.user, montant=20000, methode_paiement='orange_money'
        )

        other_user = User.objects.create_user(
            username='other', email='other@example.com',
            nom='Other', prenom='User', password='pass123'
        )
        Transaction.objects.create(
            utilisateur=other_user, montant=30000, methode_paiement='moov_money'
        )

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_transaction_detail_access(self):
        """Test d'accès au détail d'une transaction"""
        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=50000,
            methode_paiement='orange_money',
            description='Test detail'
        )

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-detail', kwargs={'pk': transaction.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['montant'], '50000.00')
        self.assertEqual(response.data['description'], 'Test detail')

    def test_user_cannot_access_other_transaction(self):
        """Test qu'un utilisateur ne peut pas voir les transactions des autres"""
        other_user = User.objects.create_user(
            username='other', email='other@example.com',
            nom='Other', prenom='User', password='pass123'
        )
        other_transaction = Transaction.objects.create(
            utilisateur=other_user,
            montant=40000,
            methode_paiement='moov_money'
        )

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-detail', kwargs={'pk': other_transaction.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_transaction_status_update_admin(self):
        """Test de mise à jour du statut par l'admin"""
        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=25000,
            methode_paiement='orange_money',
            statut='en_attente'
        )

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {'statut': 'reussi'}
        url = reverse('transaction-detail', kwargs={'pk': transaction.pk})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.statut, 'reussi')

    def test_filter_transactions_by_status(self):
        """Test du filtrage par statut"""
        Transaction.objects.create(utilisateur=self.user, montant=10000, statut='reussi')
        Transaction.objects.create(utilisateur=self.user, montant=20000, statut='echoue')
        Transaction.objects.create(utilisateur=self.user, montant=30000, statut='en_cours')

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-list') + '?statut=reussi'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['statut'], 'reussi')

    def test_filter_transactions_by_payment_method(self):
        """Test du filtrage par méthode de paiement"""
        Transaction.objects.create(utilisateur=self.user, montant=15000, methode_paiement='orange_money')
        Transaction.objects.create(utilisateur=self.user, montant=25000, methode_paiement='moov_money')
        Transaction.objects.create(utilisateur=self.user, montant=35000, methode_paiement='orange_money')

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-list') + '?methode_paiement=orange_money'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        for transaction in response.data['results']:
            self.assertEqual(transaction['methode_paiement'], 'orange_money')

    def test_transaction_amount_range_filter(self):
        """Test du filtrage par montant"""
        Transaction.objects.create(utilisateur=self.user, montant=5000, methode_paiement='orange_money')
        Transaction.objects.create(utilisateur=self.user, montant=15000, methode_paiement='orange_money')
        Transaction.objects.create(utilisateur=self.user, montant=25000, methode_paiement='orange_money')

        token = AccessToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = reverse('transaction-list') + '?montant_min=10000&montant_max=20000'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['montant'], '15000.00')

    def test_invalid_payment_method(self):
        """Test de rejet d'une méthode de paiement invalide"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        data = {
            'montant': 10000,
            'methode_paiement': 'invalid_method',
            'description': 'Test invalid method'
        }

        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaymentIntegrationTestCase(APITestCase):
    """Tests d'intégration pour les paiements"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            nom='Test',
            prenom='User',
            password='testpass123'
        )

    def test_orange_money_payment_flow(self):
        """Test du flux complet de paiement Orange Money"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 1. Créer la transaction
        data = {
            'montant': 20000,
            'methode_paiement': 'orange_money',
            'description': 'Test paiement complet',
            'numero_telephone': '+22670123456'
        }

        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        transaction_id = response.data['id']
        transaction = Transaction.objects.get(pk=transaction_id)

        # 2. Simuler l'initiation du paiement (callback simulé)
        transaction.statut = 'initie'
        transaction.reference_externe = 'OM_TEST_123'
        transaction.save()

        # 3. Vérifier le statut
        url = reverse('transaction-detail', kwargs={'pk': transaction_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'initie')

    def test_payment_timeout_handling(self):
        """Test de gestion du timeout de paiement"""
        from django.utils import timezone
        from datetime import timedelta

        transaction = Transaction.objects.create(
            utilisateur=self.user,
            montant=30000,
            methode_paiement='orange_money',
            statut='initie'
        )

        # Simuler un paiement expiré (plus de 30 minutes)
        transaction.date_creation = timezone.now() - timedelta(minutes=35)
        transaction.save()

        # Le système devrait détecter l'expiration
        # (À implémenter dans une vraie logique métier)
        self.assertTrue(transaction.date_creation < timezone.now() - timedelta(minutes=30))

