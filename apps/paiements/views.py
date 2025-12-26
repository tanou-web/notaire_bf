from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import PaiementsTransaction
from .serializers import PaiementSerializer, PaiementCreateSerializer, WebhookSerializer
from apps.demandes.models import DemandesDemande


class PaiementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaiementsTransaction.objects.all().order_by('-date_creation')
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_transaction(self, request):
        serializer = PaiementCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            tx = serializer.save()

        return Response(PaiementSerializer(tx).data, status=status.HTTP_201_CREATED)


class PaiementWebhookAPIView(APIView):
    """Endpoint public (no auth) used by the payment provider to notify status changes.

    This is a mock-style implementation: it accepts POST with 'reference' and 'statut'.
    In production, validate signatures and provider payloads.
    """
    permission_classes = []

    def post(self, request):
        # Valider et normaliser le payload via le serializer de webhook
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        ref = payload.get('reference')
        statut_norm = payload.get('statut_normalise') or payload.get('statut')

        try:
            tx = PaiementsTransaction.objects.get(reference=ref)
        except PaiementsTransaction.DoesNotExist:
            return Response({'detail': 'transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update transaction and demande atomically
        with transaction.atomic():
            tx.statut = statut_norm
            # sauvegarder le payload d'origine dans donnees_api
            tx.donnees_api = tx.donnees_api or {}
            tx.donnees_api['webhook_payload'] = request.data

            if statut_norm == 'reussi':
                from django.utils import timezone
                tx.date_validation = timezone.now()
                tx.save()

                # Propager sur la demande
                demande = tx.demande
                demande.statut = 'en_attente_traitement'
                demande.save()
            else:
                tx.save()

        return Response({'detail': 'ok'})
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import get_object_or_404
import json

from notaires_bf import settings

# Import des services
from .services import get_payment_service
from .models import PaiementsTransaction
from .serializers import TransactionSerializer, TransactionCreateSerializer


class InitierPaiementView(APIView):
    """Vue pour initier un paiement avec l'API de l'opérateur"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        from demandes.models import DemandesDemande
        
        demande_id = request.data.get('demande_id')
        type_paiement = request.data.get('type_paiement')
        
        if not demande_id or not type_paiement:
            return Response(
                {'error': 'demande_id et type_paiement sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer la demande
            demande = DemandesDemande.objects.get(
                id=demande_id, 
                utilisateur=request.user,
                statut='attente_paiement'  # Vérifier que la demande est en attente de paiement
            )
            
            # Vérifier si une transaction existe déjà
            if hasattr(demande, 'paiementstransaction'):
                return Response(
                    {'error': 'Une transaction existe déjà pour cette demande'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer la transaction
            transaction = PaiementsTransaction.objects.create(
                demande=demande,
                type_paiement=type_paiement,
                montant=demande.montant_total,
                commission=demande.montant_total * 0.03,
                statut='initie',
                donnees_api={},
                date_creation=timezone.now(),
                date_maj=timezone.now()
            )
            
            # Générer une référence si non fournie
            if not transaction.reference:
                transaction.reference = f"TXN-{int(timezone.now().timestamp())}-{demande.id}"
                transaction.save()
            
            # Obtenir le service de paiement et initier le paiement
            try:
                payment_service = get_payment_service(transaction)
                payment_result = payment_service.initiate_payment()
                
                if not payment_result['success']:
                    # Si l'initiation échoue, marquer la transaction comme échec
                    transaction.statut = 'echec'
                    transaction.donnees_api = payment_result.get('api_data', {})
                    transaction.save()
                    
                    return Response({
                        'status': 'error',
                        'message': f"Échec de l'initiation du paiement: {payment_result.get('error')}",
                        'transaction': TransactionSerializer(transaction).data
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Sauvegarder les données de l'API
                transaction.donnees_api = payment_result.get('api_data', {})
                transaction.save()
                
                # Retourner l'URL de paiement
                return Response({
                    'status': 'success',
                    'message': 'Paiement initié avec succès',
                    'transaction': TransactionSerializer(transaction).data,
                    'payment_url': payment_result['payment_url'],
                    'transaction_id': payment_result.get('transaction_id'),
                    'next_step': 'Redirigez l\'utilisateur vers payment_url pour effectuer le paiement'
                })
                
            except Exception as e:
                transaction.statut = 'echec'
                transaction.donnees_api = {'error': str(e)}
                transaction.save()
                
                return Response({
                    'status': 'error',
                    'message': f'Erreur lors de l\'initiation du paiement: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except DemandesDemande.DoesNotExist:
            return Response(
                {'error': 'Demande non trouvée ou non éligible au paiement'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookView(APIView):
    """Endpoint pour les webhooks des opérateurs de paiement"""
    permission_classes = []  # Pas d'authentification requise (les webhooks viennent des opérateurs)
    
    def post(self, request, provider):
        """
        Webhook pour recevoir les notifications des opérateurs
        provider: 'orange_money' ou 'moov_money'
        """
        try:
            # Récupérer la signature du header
            signature = request.headers.get('X-Signature') or request.headers.get('Signature')
            
            # Récupérer les données
            data = request.data
            
            # Pour Orange Money, l'ID de transaction est généralement dans 'order_id'
            # Pour Moov Money, c'est dans 'transactionId'
            transaction_reference = None
            
            if provider == 'orange_money':
                transaction_reference = data.get('order_id') or data.get('reference')
            elif provider == 'moov_money':
                transaction_reference = data.get('transactionId') or data.get('orderId')
            
            if not transaction_reference:
                return Response(
                    {'error': 'Référence de transaction non trouvée'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer la transaction
            transaction = get_object_or_404(
                PaiementsTransaction, 
                reference=transaction_reference
            )
            
            # Vérifier que le provider correspond
            if transaction.type_paiement != provider:
                return Response(
                    {'error': 'Provider incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtenir le service de paiement
            payment_service = get_payment_service(transaction)
            
            # Vérifier la signature (sécurité importante!)
            if signature and not payment_service.verify_webhook_signature(data, signature):
                return Response(
                    {'error': 'Signature invalide'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Mapper les statuts selon le provider
            status_mapping = {
                'orange_money': {
                    'SUCCESS': 'reussi',
                    'FAILED': 'echec',
                    'PENDING': 'en_attente',
                    'CANCELLED': 'echec'
                },
                'moov_money': {
                    'COMPLETED': 'reussi',
                    'FAILED': 'echec',
                    'PENDING': 'en_attente',
                    'CANCELLED': 'echec'
                }
            }
            
            # Déterminer le nouveau statut
            provider_status = data.get('status') or data.get('paymentStatus')
            new_status = status_mapping[provider].get(provider_status, 'en_attente')
            
            # Mettre à jour la transaction
            old_status = transaction.statut
            transaction.statut = new_status
            
            # Si le statut passe à 'reussi', mettre à jour la date de validation
            if new_status == 'reussi' and old_status != 'reussi':
                transaction.date_validation = timezone.now()
                
                # Mettre à jour le statut de la demande
                demande = transaction.demande
                demande.statut = 'en_attente_traitement'
                demande.save()
            
            # Sauvegarder les données du webhook
            webhook_data = transaction.donnees_api or {}
            webhook_data[f'webhook_{provider}'] = {
                'received_at': timezone.now().isoformat(),
                'data': data,
                'signature': signature
            }
            transaction.donnees_api = webhook_data
            
            transaction.save()
            
            # Log pour le débogage
            print(f"Webhook {provider}: Transaction {transaction.reference} mise à jour de {old_status} à {new_status}")
            
            return Response({
                'status': 'success',
                'message': f'Transaction {transaction.reference} mise à jour',
                'transaction_id': transaction.id,
                'reference': transaction.reference,
                'new_status': new_status
            })
        
        except Exception as e:
            print(f"Erreur webhook {provider}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifierPaiementView(APIView):
    """Vérifier manuellement le statut d'un paiement"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        transaction_reference = request.data.get('transaction_reference')
        
        if not transaction_reference:
            return Response(
                {'error': 'transaction_reference est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction = get_object_or_404(
                PaiementsTransaction, 
                reference=transaction_reference,
                demande__utilisateur=request.user  # L'utilisateur ne peut vérifier que ses transactions
            )
            
            # Obtenir le service de paiement
            payment_service = get_payment_service(transaction)
            
            # Trouver l'ID de transaction dans les données API
            transaction_id = None
            api_data = transaction.donnees_api or {}
            
            if transaction.type_paiement == 'orange_money':
                transaction_id = api_data.get('transaction_id') or api_data.get('data', {}).get('transaction_id')
            elif transaction.type_paiement == 'moov_money':
                transaction_id = api_data.get('transactionId') or api_data.get('data', {}).get('transactionId')
            
            if not transaction_id:
                return Response({
                    'error': 'ID de transaction non trouvé'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier le paiement avec l'API du provider
            verification_result = payment_service.verify_payment(transaction_id)
            
            if verification_result['success']:
                old_status = transaction.statut
                new_status = verification_result['status']
                
                # Mettre à jour le statut si différent
                if new_status != old_status:
                    transaction.statut = new_status
                    
                    if new_status == 'reussi' and old_status != 'reussi':
                        transaction.date_validation = timezone.now()
                        
                        # Mettre à jour le statut de la demande
                        demande = transaction.demande
                        demande.statut = 'en_attente_traitement'
                        demande.save()
                    
                    # Mettre à jour les données API
                    verification_data = transaction.donnees_api or {}
                    verification_data['verification'] = {
                        'verified_at': timezone.now().isoformat(),
                        'result': verification_result.get('api_data', {})
                    }
                    transaction.donnees_api = verification_data
                    
                    transaction.save()
                
                return Response({
                    'status': 'success',
                    'message': f'Transaction vérifiée: {new_status}',
                    'transaction': TransactionSerializer(transaction).data,
                    'verification_result': verification_result
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Erreur de vérification: {verification_result.get("error")}',
                    'transaction': TransactionSerializer(transaction).data
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CallbackView(APIView):
    """Callback pour la redirection après paiement"""
    permission_classes = []  # Accessible à tous
    
    def get(self, request):
        """
        Gérer le retour de l'utilisateur après paiement
        Exemple d'URL: /api/paiements/callback/?transaction_id=TXN-123&status=success
        """
        transaction_id = request.GET.get('transaction_id')
        status_param = request.GET.get('status', 'pending')
        
        if not transaction_id:
            return Response(
                {'error': 'transaction_id manquant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction = get_object_or_404(
                PaiementsTransaction,
                reference=transaction_id
            )
            
            # Rediriger vers la page de confirmation appropriée
            frontend_url = settings.FRONTEND_URL
            
            if transaction.statut == 'reussi':
                redirect_url = f"{frontend_url}/paiement/success/{transaction_id}"
            elif transaction.statut == 'echec':
                redirect_url = f"{frontend_url}/paiement/failed/{transaction_id}"
            else:
                redirect_url = f"{frontend_url}/paiement/pending/{transaction_id}"
            
            # Redirection HTTP
            from django.shortcuts import redirect
            return redirect(redirect_url)
        
        except Exception as e:
            # En cas d'erreur, rediriger vers une page d'erreur générique
            frontend_url = settings.FRONTEND_URL
            error_url = f"{frontend_url}/paiement/error?message={str(e)}"
            from django.shortcuts import redirect
            return redirect(error_url)