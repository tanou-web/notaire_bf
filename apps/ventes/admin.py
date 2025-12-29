# apps/ventes/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import VenteSticker, DemandeVente, Paiement, AvisClient, CodePromo, Vente


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


# ========================================
# 4. VENTE
# ========================================
@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'sticker_display', 'client_email', 'notaire_display', 'quantite', 'prix_unitaire', 'montant_total', 'est_payee', 'statut')
    list_filter = ('statut', 'est_payee', 'date_vente')
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


# ========================================
# 5. PAIEMENTS
# ========================================
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'type_paiement', 'montant', 'statut', 'date_creation', 'demande_display', 'vente_sticker_display')
    list_filter = ('type_paiement', 'statut', 'date_creation')
    search_fields = ('reference', 'demande__reference', 'vente_sticker__reference')
    readonly_fields = ('reference', 'date_creation', 'date_validation')

    def demande_display(self, obj):
        return obj.demande.reference if obj.demande else "-"
    demande_display.short_description = 'Demande'

    def vente_sticker_display(self, obj):
        return obj.vente_sticker.reference if obj.vente_sticker else "-"
    vente_sticker_display.short_description = 'Vente Sticker'


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
        return obj.sticker.reference if obj.sticker else "-"
    sticker_display.short_description = 'Sticker'

    def demande_display(self, obj):
        return obj.demande.reference if obj.demande else "-"
    demande_display.short_description = 'Demande'

