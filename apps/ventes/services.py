# apps/ventes/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Q, F
from datetime import timedelta
import uuid
from django.conf import settings

from .models import (
    VenteSticker, VentesSticker, Demande, 
    Paiement, User
)
from .serializers import DemandeCreateSerializer


class VenteStickerService:
    """Service pour la gestion des ventes de stickers"""
    
    @staticmethod
    @transaction.atomic
    def creer_vente(data, request=None):
        """
        Créer une vente de sticker liée à un notaire
        """
        # Validation des champs requis
        required_fields = ['sticker_id', 'notaire_id', 'quantite', 'client_nom', 'client_email']
        for field in required_fields:
            if not data.get(field):
                raise ValidationError({field: 'Ce champ est requis'})
        
        # Normalisation email
        if 'client_email' in data:
            data['client_email'] = data['client_email'].lower().strip()
        
        # Vérification du stock (avec verrouillage)
        sticker = VentesSticker.objects.select_for_update().get(
            id=data['sticker_id'],
            actif=True
        )
        
        if sticker.quantite < data['quantite']:
            raise ValidationError({
                'quantite': f'Stock insuffisant. Disponible: {sticker.quantite}'
            })
        
        # Prix figé à la date de vente (historique)
        prix_unitaire = sticker.prix_ttc
        
        # Création de la vente
        vente = VenteSticker.objects.create(
            sticker=sticker,
            notaire_id=data['notaire_id'],
            quantite=data['quantite'],
            prix_unitaire=prix_unitaire,
            montant_total=prix_unitaire * data['quantite'],
            client_nom=data['client_nom'],
            client_email=data['client_email'],
            client_contact=data.get('client_contact', ''),
            token_acces=uuid.uuid4() if data.get('avec_suivi') else None
        )
        
        # Décrémentation atomique du stock
        sticker.quantite = F('quantite') - data['quantite']
        sticker.save(update_fields=['quantite'])
        sticker.refresh_from_db()
        
        return {
            'vente': vente,
            'stock_restant': sticker.quantite,
            'prix_unitaire_fige': prix_unitaire
        }


class DemandeService:
    """Service pour la gestion des demandes"""
    
    @staticmethod
    @transaction.atomic
    def creer_demande_sans_compte(data, request=None):
        """
        Créer une demande sans compte utilisateur
        """
        # Normalisation email si présent
        if 'client_email' in data and data['client_email']:
            data['client_email'] = data['client_email'].lower().strip()
        
        serializer = DemandeCreateSerializer(data=data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        
        # Validation du code promo si fourni
        code_promo = None
        if 'code_promo' in data:
            # Import ici pour éviter les dépendances circulaires
            from .services import CodePromoService
            code_promo = CodePromoService.valider_code_promo(
                code=data['code_promo'],
                type_utilisateur='client_externe'
            )
        
        demande = serializer.save()
        
        # Générer token d'accès pour suivi sans compte
        demande.token_acces = str(uuid.uuid4())
        demande.lien_suivi = f"{settings.FRONTEND_URL}/suivi/{demande.token_acces}"
        demande.save()
        
        return {
            'demande': demande,
            'code_promo_applique': code_promo.code if code_promo else None
        }
    
    @staticmethod
    @transaction.atomic
    def attribuer_a_notaire(demande_id, notaire_id):
        """
        Attribuer une demande à un notaire
        
        Args:
            demande_id: ID de la demande
            notaire_id: ID du notaire
        """
        demande = get_object_or_404(Demande, id=demande_id)
        
        # Vérifier que la demande est payée
        if not demande.est_payee:
            raise ValidationError("La demande doit être payée avant attribution")
        
        if demande.statut != 'en_traitement':
            raise ValidationError("La demande doit être en traitement")
        
        notaire = get_object_or_404(User, id=notaire_id, role='notaire')
        
        # Vérifier la disponibilité du notaire
        demandes_actives = Demande.objects.filter(
            notaire=notaire,
            statut__in=['en_traitement', 'en_attente_notaire']
        ).count()
        
        if demandes_actives >= 5:  # Limite de 5 demandes actives
            raise ValidationError("Ce notaire a atteint sa limite de demandes actives")
        
        # Attribution
        demande.notaire = notaire
        demande.statut = 'en_attente_notaire'
        demande.save()
        
        # Mise à jour disponibilité notaire
        notaire.is_available = False
        notaire.save(update_fields=['is_available'])
        
        # Envoyer notification au notaire
        from .services import NotificationService
        NotificationService.notifier_notaire_nouvelle_demande(notaire, demande)
        
        return demande


class PaiementService:
    """Service pour la gestion des paiements"""
    
    @staticmethod
    def initier_paiement(type_transaction, reference, type_paiement='orange_money', request=None):
        """
        Initier un paiement pour une demande ou vente
        
        Args:
            type_transaction: 'demande' ou 'vente_sticker'
            reference: Référence de la transaction
            type_paiement: Type de paiement (orange_money, mtn_money, etc.)
        """
        # Récupérer la transaction
        if type_transaction == 'demande':
            transaction = get_object_or_404(Demande, reference=reference)
        elif type_transaction == 'vente_sticker':
            transaction = get_object_or_404(VenteSticker, reference=reference)
        else:
            raise ValidationError({'type_transaction': 'Type invalide'})
        
        # Vérifier si pas déjà payé
        if hasattr(transaction, 'est_payee') and transaction.est_payee:
            raise ValidationError('Transaction déjà payée')
        
        # Créer l'enregistrement de paiement
        paiement = Paiement.objects.create(
            reference=uuid.uuid4().hex[:12].upper(),
            type_paiement=type_paiement,
            montant=transaction.montant_total,
            statut='en_attente',
            demande=transaction if type_transaction == 'demande' else None,
            vente_sticker=transaction if type_transaction == 'vente_sticker' else None
        )
        
        # Générer URL de paiement
        payment_url = PaiementService._generer_url_paiement(
            paiement, type_paiement
        )
        
        return {
            'paiement': paiement,
            'payment_url': payment_url
        }
    
    @staticmethod
    def _generer_url_paiement(paiement, type_paiement):
        """
        Générer l'URL de paiement selon le type
        """
        if not hasattr(settings, 'PAYMENT_GATEWAY_URL'):
            return None
        
        base_url = settings.PAYMENT_GATEWAY_URL
        
        if type_paiement in ['orange_money', 'mtn_money']:
            return f"{base_url}/mobile/initiate/{paiement.reference}"
        elif type_paiement == 'carte_bancaire':
            return f"{base_url}/card/initiate/{paiement.reference}"
        elif type_paiement == 'especes':
            return f"{settings.FRONTEND_URL}/paiement-especes/{paiement.reference}"
        
        return None


class StatistiquesService:
    """Service pour les statistiques"""
    
    @staticmethod
    def statistiques_notaire(notaire_id, date_debut=None, date_fin=None):
        """
        Statistiques pour un notaire spécifique
        """
        if not date_debut:
            date_debut = timezone.now() - timedelta(days=30)
        if not date_fin:
            date_fin = timezone.now()
        
        # Ventes stickers
        ventes_stats = VenteSticker.objects.filter(
            notaire_id=notaire_id,
            date_vente__range=[date_debut, date_fin]
        ).aggregate(
            total_ventes=Count('id'),
            total_montant=Sum('montant_total'),
            stickers_vendus=Sum('quantite')
        )
        
        # Demandes
        demandes_stats = Demande.objects.filter(
            notaire_id=notaire_id,
            created_at__range=[date_debut, date_fin]
        ).aggregate(
            total_demandes=Count('id'),
            demandes_terminees=Count('id', filter=Q(statut='termine')),
            total_montant=Sum('montant_total')
        )
        
        # Calcul CA total
        ca_ventes = ventes_stats['total_montant'] or 0
        ca_demandes = demandes_stats['total_montant'] or 0
        ca_total = ca_ventes + ca_demandes
        
        return {
            'notaire_id': notaire_id,
            'periode': {'debut': date_debut, 'fin': date_fin},
            'ventes_stickers': ventes_stats,
            'demandes_documents': demandes_stats,
            'chiffre_affaires_total': float(ca_total),
            'ventes_par_sticker': StatistiquesService._ventes_par_sticker(
                notaire_id, date_debut, date_fin
            )
        }
    
    @staticmethod
    def _ventes_par_sticker(notaire_id, date_debut, date_fin):
        """
        Détail des ventes par type de sticker
        """
        return list(
            VenteSticker.objects.filter(
                notaire_id=notaire_id,
                date_vente__range=[date_debut, date_fin]
            ).values('sticker__nom').annotate(
                quantite_vendue=Sum('quantite'),
                montant_total=Sum('montant_total')
            ).order_by('-quantite_vendue')
        )


class NotificationService:
    """Service pour les notifications"""
    
    @staticmethod
    def notifier_notaire_nouvelle_demande(notaire, demande):
        """
        Notifier un notaire d'une nouvelle demande
        """
        # Ici, vous intégrerez votre système de notifications
        # Ex: email, SMS, push notification, etc.
        
        # Exemple d'envoi d'email
        subject = "Nouvelle demande de document"
        message = f"""
        Bonjour {notaire.get_full_name()},
        
        Une nouvelle demande vous a été attribuée :
        - Référence : {demande.reference}
        - Document : {demande.document.nom}
        - Client : {demande.client_nom}
        - Montant : {demande.montant_total} FCFA
        
        Connectez-vous à votre espace pour traiter cette demande.
        """
        
        # Envoi réel d'email (à configurer)
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [notaire.email])
        
        # Pour l'instant, log seulement
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Notification envoyée à {notaire.email}: {message[:100]}...")


class CodePromoService:
    """Service pour la gestion des codes promotionnels"""
    
    @staticmethod
    def valider_code_promo(code, type_utilisateur):
        """
        Valider un code promotionnel
        """
        # Implémentation simplifiée
        from .models import CodePromo
        
        try:
            code_promo = CodePromo.objects.get(
                code=code,
                est_actif=True,
                date_expiration__gte=timezone.now(),
                type_utilisateur=type_utilisateur
            )
            
            if code_promo.utilisations >= code_promo.limite_utilisations:
                raise ValidationError("Code promo épuisé")
            
            return code_promo
        except CodePromo.DoesNotExist:
            raise ValidationError("Code promo invalide")