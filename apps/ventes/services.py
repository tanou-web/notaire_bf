from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
from .models import VentesSticker, Demande, Client


class StockService:
    """Service de gestion du stock."""
    
    @staticmethod
    def verifier_stock(sticker_id, quantite_demandee):
        """Vérifie si le stock est suffisant."""
        try:
            sticker = VentesSticker.objects.get(id=sticker_id)
            return sticker.quantite >= quantite_demandee
        except VentesSticker.DoesNotExist:
            return False
    
    @staticmethod
    def decrementer_stock(sticker_id, quantite):
        """Décrémente le stock."""
        try:
            sticker = VentesSticker.objects.get(id=sticker_id)
            sticker.quantite -= quantite
            sticker.date_derniere_vente = timezone.now()
            sticker.save()
            return True
        except VentesSticker.DoesNotExist:
            return False
    
    @staticmethod
    def incrementer_stock(sticker_id, quantite):
        """Incrémente le stock."""
        try:
            sticker = VentesSticker.objects.get(id=sticker_id)
            sticker.quantite += quantite
            sticker.save()
            return True
        except VentesSticker.DoesNotExist:
            return False
    
    @staticmethod
    def produits_en_rupture():
        """Retourne les produits en rupture de stock."""
        return VentesSticker.objects.filter(
            quantite=0,
            actif=True
        )
    
    @staticmethod
    def produits_bas_stock():
        """Retourne les produits avec stock faible."""
        return VentesSticker.objects.filter(
            quantite__lte=models.F('stock_minimum'),
            quantite__gt=0,
            actif=True
        )


class FacturationService:
    """Service de facturation."""
    
    @staticmethod
    def calculer_tva(montant_ht, taux_tva=20.0):
        """Calcule la TVA."""
        return montant_ht * (taux_tva / 100)
    
    @staticmethod
    def calculer_ttc(montant_ht, taux_tva=20.0):
        """Calcule le TTC."""
        return montant_ht * (1 + taux_tva / 100)
    
    @staticmethod
    def generer_facture(demande):
        """Génère une facture pour une demande."""
        from .models import VentesFacture
        
        # Calculer les totaux
        montant_ht = demande.sous_total_ht
        tva = demande.montant_tva
        montant_ttc = demande.montant_total_ttc
        
        # Créer la facture
        facture = VentesFacture.objects.create(
            demande=demande,
            client=demande.client,
            montant_ht=montant_ht,
            tva=tva,
            montant_ttc=montant_ttc,
            date_emission=timezone.now().date()
        )
        
        return facture


class StatistiquesService:
    """Service de statistiques de vente."""
    
    @staticmethod
    def ventes_par_periode(date_debut, date_fin):
        """Statistiques des ventes par période."""
        demandes = Demande.objects.filter(
            date_creation__range=[date_debut, date_fin],
            statut__in=['confirmee', 'expediee', 'livree']
        )
        
        total_ventes = demandes.count()
        total_montant = demandes.aggregate(total=models.Sum('montant_total_ttc'))['total'] or Decimal('0')
        moyenne_panier = total_montant / total_ventes if total_ventes > 0 else Decimal('0')
        
        return {
            'periode': f"{date_debut} - {date_fin}",
            'total_ventes': total_ventes,
            'total_montant': total_montant,
            'moyenne_panier': moyenne_panier,
            'demandes_par_statut': dict(demandes.values('statut').annotate(
                count=models.Count('id')
            ).values_list('statut', 'count'))
        }
    
    @staticmethod
    def top_produits(limit=10):
        """Top des produits les plus vendus."""
        from .models import LigneDemande
        
        top = LigneDemande.objects.filter(
            demande__statut__in=['confirmee', 'expediee', 'livree']
        ).values(
            'sticker__code', 'sticker__nom'
        ).annotate(
            total_vendu=models.Sum('quantite'),
            total_montant=models.Sum(models.F('prix_unitaire_ht') * models.F('quantite'))
        ).order_by('-total_vendu')[:limit]
        
        return list(top)
    
    @staticmethod
    def clients_actifs(limit=10):
        """Clients les plus actifs."""
        clients = Client.objects.filter(
            est_actif=True,
            nombre_commandes__gt=0
        ).order_by('-montant_total_achats')[:limit]
        
        result = []
        for client in clients:
            result.append({
                'client': client.nom_complet,
                'nombre_commandes': client.nombre_commandes,
                'montant_total': client.montant_total_achats,
                'moyenne_panier': client.moyenne_panier,
                'est_fidele': client.est_fidele
            })
        
        return result


class NotificationService:
    """Service de notifications."""
    
    @staticmethod
    def notifier_stock_faible(sticker):
        """Notifie quand le stock est faible."""
        # Implémentez votre système de notification ici
        # Email, SMS, notification interne, etc.
        print(f"Alerte stock faible: {sticker.nom} (Stock: {sticker.quantite})")
    
    @staticmethod
    def notifier_commande_confirmee(demande):
        """Notifie la confirmation d'une commande."""
        print(f"Commande confirmée: {demande.numero} - {demande.client.nom_complet}")
    
    @staticmethod
    def notifier_facture_emise(facture):
        """Notifie l'émission d'une facture."""
        print(f"Facture émise: {facture.numero} - {facture.montant_ttc}€")