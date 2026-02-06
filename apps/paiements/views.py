from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from .models import PaiementsTransaction
from .serializers import PaiementSerializer, PaiementCreateSerializer
from apps.demandes.models import DemandesDemande
from apps.communications.services import SMSService


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

            if statut_norm == 'validee':
                from django.utils import timezone
                tx.date_validation = timezone.now()
                tx.save()

                # Propager sur la demande
                demande = tx.demande
                demande.statut = 'en_attente_traitement'
                demande.save()

                # Envoyer un SMS de confirmation de paiement
                try:
                    # Récupérer le numéro de téléphone du demandeur
                    user_phone = None
                    if hasattr(demande, 'demandeur') and demande.demandeur:
                        user_phone = getattr(demande.demandeur, 'telephone', None)

                    if user_phone:
                        SMSService.send_payment_confirmation_sms(
                            phone_number=user_phone,
                            transaction_reference=tx.reference,
                            amount=str(tx.montant),
                            user_name=getattr(demande.demandeur, 'nom', None)
                        )
                except Exception as e:
                    # Ne pas échouer le webhook si l'envoi SMS échoue
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erreur envoi SMS confirmation paiement {tx.reference}: {e}")
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
from .serializers import (
    PaiementSerializer, 
    PaiementCreateSerializer, 
    PaiementUpdateSerializer,
    WebhookSerializer,
    InitierPaiementResponseSerializer,
    StatistiquesPaiementSerializer
)

class InitierPaiementView(APIView):
    """Vue pour initier un paiement avec l'API de l'opérateur"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        from apps.demandes.models import DemandesDemande
        
        demande_id = request.data.get('demande_id')
        type_paiement = request.data.get('type_paiement')
        
        if not demande_id or not type_paiement:
            return Response(
                {'error': 'demande_id et type_paiement sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer la demande
            # On autorise tout le monde à payer une demande en attente de paiement
            # C'est une opération "write-only" (initiation) sécuritaire
            demande = DemandesDemande.objects.get(
                id=demande_id, 
                statut='attente_paiement'  # Vérifier que la demande est en attente de paiement
            )
            
            # Vérifier si une transaction existe déjà
            if hasattr(demande, 'paiementstransaction'):
                return Response(
                    {'error': 'Une transaction existe déjà pour cette demande'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer la transaction sans commission ajoutée (commission mise à 0)
            transaction = PaiementsTransaction.objects.create(
                demande=demande,
                type_paiement=type_paiement,
                montant=demande.montant_total,
                commission=0,
                statut='initiee',
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
                        'transaction': PaiementSerializer(transaction).data
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Sauvegarder les données de l'API
                transaction.donnees_api = payment_result.get('api_data', {})
                transaction.save()
                
                # Retourner l'URL de paiement
                return Response({
                    'status': 'success',
                    'message': 'Paiement initié avec succès',
                    'transaction': PaiementSerializer(transaction).data,
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
            signature = request.headers.get('X-Signature') or \
                        request.headers.get('Signature') or \
                        request.headers.get('x-webhook-hash')
            
            # Récupérer les données
            data = request.data
            
            # Pour Orange Money, l'ID de transaction est généralement dans 'order_id'
            # Pour Moov Money, c'est dans 'transactionId'
            transaction_reference = None
            
            if provider == 'yengapay':
                transaction_reference = data.get('reference')
            else:
                # Anciens providers (Orange/Moov) - fallback sur reference
                transaction_reference = data.get('reference') or data.get('order_id') or data.get('transactionId')
            
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
                'yengapay': {
                    'DONE': 'validee',
                    'SUCCESS': 'validee',
                    'FAILED': 'echouee',
                    'PENDING': 'en_attente',
                    'CANCELLED': 'echouee'
                }
            }
            
            # Fallback pour la compatibilité avec les anciens webhooks si nécessaire
            if provider not in status_mapping:
                provider_status = data.get('status') or data.get('paymentStatus')
                if provider_status in ['SUCCESS', 'COMPLETED', 'DONE']:
                    new_status = 'validee'
                elif provider_status in ['FAILED', 'CANCELLED']:
                    new_status = 'echouee'
                else:
                    new_status = 'en_attente'
            else:
                provider_status = data.get('status') or data.get('paymentStatus') or data.get('transactionStatus')
                new_status = status_mapping[provider].get(provider_status, 'en_attente')
            
            # Mettre à jour la transaction
            old_status = transaction.statut
            transaction.statut = new_status
            
            # Si le statut passe à 'validee', mettre à jour la date de validation
            if new_status == 'validee' and old_status != 'validee':
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

                        # Envoyer un SMS de confirmation de paiement
                        try:
                            # Récupérer le numéro de téléphone du demandeur
                            user_phone = None
                            if hasattr(demande, 'demandeur') and demande.demandeur:
                                user_phone = getattr(demande.demandeur, 'telephone', None)

                            if user_phone:
                                SMSService.send_payment_confirmation_sms(
                                    phone_number=user_phone,
                                    transaction_reference=transaction.reference,
                                    amount=str(transaction.montant),
                                    user_name=getattr(demande.demandeur, 'nom', None)
                                )
                        except Exception as e:
                            # Ne pas échouer la vérification si l'envoi SMS échoue
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"Erreur envoi SMS confirmation paiement {transaction.reference}: {e}")
                    
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
                    'transaction': PaiementSerializer(transaction).data,
                    'verification_result': verification_result
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Erreur de vérification: {verification_result.get("error")}',
                    'transaction': PaiementSerializer(transaction).data
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


class ExportRapportView(APIView):
    """
    Export des rapports financiers en PDF
    Accessible uniquement aux administrateurs
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        format_type = request.query_params.get('format', 'pdf')  # pdf ou excel
        periode = request.query_params.get('periode', '30')  # jours

        try:
            jours = int(periode)
        except ValueError:
            jours = 30

        date_debut = timezone.now() - timedelta(days=jours)

        # Récupérer les données financières
        transactions = PaiementsTransaction.objects.filter(
            date_creation__gte=date_debut
        ).select_related('demande')

        # Calculer les statistiques
        stats_globales = transactions.aggregate(
            total_montant=Sum('montant'),
            nombre_transactions=Count('id'),
            transactions_reussies=Count('id', filter=Q(statut='reussi')),
            transactions_echouees=Count('id', filter=Q(statut='echec'))
        )

        if format_type.lower() == 'pdf':
            return self._generer_pdf(transactions, stats_globales, date_debut, jours)
        else:
            return Response({"error": "Format non supporté"}, status=400)

    def _generer_pdf(self, transactions, stats, date_debut, jours):
        """Génère un rapport PDF des transactions"""

        # Créer le buffer pour le PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centré
        )

        # Titre
        titre = Paragraph(f"Rapport Financier - {jours} jours", title_style)
        elements.append(titre)
        elements.append(Spacer(1, 12))

        # Période
        periode_text = f"Période: {date_debut.date()} - {timezone.now().date()}"
        elements.append(Paragraph(periode_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Statistiques globales
        stats_data = [
            ['Métrique', 'Valeur'],
            ['Nombre total de transactions', str(stats['nombre_transactions'] or 0)],
            ['Transactions réussies', str(stats['transactions_reussies'] or 0)],
            ['Transactions échouées', str(stats['transactions_echouees'] or 0)],
            ['Montant total (€)', f"{stats['total_montant'] or 0:.2f}"],
        ]

        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 30))

        # Détail des transactions (premières 50)
        elements.append(Paragraph("Détail des transactions", styles['Heading2']))
        elements.append(Spacer(1, 12))

        transactions_data = [['Date', 'Référence', 'Montant', 'Statut', 'Méthode']]
        for tx in transactions[:50]:  # Limiter à 50 pour la lisibilité
            transactions_data.append([
                tx.date_creation.strftime('%d/%m/%Y %H:%M'),
                tx.reference[:20] + '...' if len(tx.reference) > 20 else tx.reference,
                f"{tx.montant:.2f} €",
                tx.statut.title(),
                tx.methode_paiement or 'N/A'
            ])

        if len(transactions) > 50:
            transactions_data.append(['...', '...', '...', '...', '...'])

        tx_table = Table(transactions_data)
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(tx_table)

        # Génération du PDF
        doc.build(elements)

        # Préparer la réponse
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_financier_{jours}j_{timezone.now().date()}.pdf"'

        return response