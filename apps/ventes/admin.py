# apps/ventes/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import VenteSticker, DemandeVente, Paiement, AvisClient, CodePromo, ReferenceSticker, VenteStickerNotaire


# ========================================
# 1. CODE PROMO
# ========================================
@admin.register(CodePromo)
class CodePromoAdmin(admin.ModelAdmin):
    list_display = ('code', 'taux_reduction', 'actif', 'date_expiration', 'est_valide_display')
    list_filter = ('actif',)
    search_fields = ('code',)
    readonly_fields = ()
    
    def est_valide_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.est_valide() else 'red',
            'Valide' if obj.est_valide() else 'Expiré'
        )
    est_valide_display.short_description = 'Statut'


# ========================================
# 2. DEMANDE DE VENTE
# ========================================
@admin.register(DemandeVente)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('reference', 'client_email', 'notaire_display', 'montant_total', 'est_payee', 'statut', 'created_at')
    list_filter = ('statut', 'est_payee', 'created_at')
    search_fields = ('reference', 'client_email')
    readonly_fields = ('reference', 'token_acces', 'created_at', 'updated_at')

    def notaire_display(self, obj):
        if obj.notaire:
            return f"{obj.notaire.nom} {obj.notaire.prenom}"
        return "Non attribué"
    notaire_display.short_description = 'Notaire'


# ========================================
# 3. VENTE STICKER
# ========================================
@admin.register(VenteSticker)
class VenteStickerAdmin(admin.ModelAdmin):
    list_display = ('reference', 'sticker_display', 'client_email', 'notaire_display', 'quantite', 'prix_unitaire', 'montant_total', 'est_payee', 'statut')
    list_filter = ('statut', 'est_payee')
    search_fields = ('reference', 'client_email', 'sticker__nom')
    readonly_fields = ('reference', 'token_acces', 'date_vente', 'montant_total')

    def sticker_display(self, obj):
        return obj.sticker.nom if obj.sticker else "N/A"
    sticker_display.short_description = 'Sticker'

    def notaire_display(self, obj):
        if obj.notaire:
            return f"{obj.notaire.nom} {obj.notaire.prenom}"
        return "Non attribué"
    notaire_display.short_description = 'Notaire'


#
# ========================================
# 5. PAIEMENTS
# ========================================
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'type_paiement', 'montant', 'statut', 'date_creation', 'demande_display', 'vente_sticker_display')
    list_filter = ('type_paiement', 'statut', 'date_creation')
    search_fields = ('reference', 'demande__reference', 'vente_sticker__reference')
    readonly_fields = ('reference', 'date_creation', 'date_validation')
    
    def vente_sticker_display(self, obj):
        return obj.vente_sticker.reference if obj.vente_sticker else "-"
    vente_sticker_display.short_description = 'Vente Sticker'


    def statut_colore(self, obj):
        colors = {
            'reussi': 'green',
            'echoue': 'red',
            'en_attente': 'orange'
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.statut, 'black'),
            obj.get_statut_display()
        )

    statut_colore.short_description = 'Statut'


    def demande_display(self, obj):
        return obj.demande.reference if obj.demande else "-"
    demande_display.short_description = 'Demande'


# ========================================
# 7. STICKERS NOTAIRES
# ========================================
@admin.register(ReferenceSticker)
class ReferenceStickerAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix_unitaire', 'total_stock', 'created_at')
    search_fields = ('nom',)

@admin.register(VenteStickerNotaire)
class VenteStickerNotaireAdmin(admin.ModelAdmin):
    list_display = (
        'reference', 'notaire_display', 'type_sticker', 'quantite', 
        'plage_debut', 'plage_fin', 'montant_total', 'montant_paye', 
        'reste_a_payer', 'date_vente'
    )
    list_filter = ('date_vente', 'type_sticker')
    search_fields = ('reference', 'notaire__nom', 'plage_debut', 'plage_fin')
    readonly_fields = ('reference', 'montant_total', 'reste_a_payer', 'created_at', 'updated_at')
    
    def notaire_display(self, obj):
        return f"{obj.notaire.nom} {obj.notaire.prenom}"
    notaire_display.short_description = 'Notaire'


# ========================================
# 6. AVIS CLIENT
# ========================================
@admin.register(AvisClient)
class AvisClientAdmin(admin.ModelAdmin):
    list_display = ('client_email', 'sticker_display', 'demande_display', 'note', 'est_valide', 'created_at')
    list_filter = ('est_valide', 'created_at')
    search_fields = ('client_email',)
    readonly_fields = ('created_at',)

    def sticker_display(self, obj):
     return obj.sticker.sticker.nom if obj.sticker and obj.sticker.sticker else "-"


    def demande_display(self, obj):
        return obj.demande.reference if obj.demande else "-"
    demande_display.short_description = 'Demande'