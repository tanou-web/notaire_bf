from django.contrib import admin
from django.utils.html import format_html
from .models import (
    VentesSticker, Client, Demande, LigneDemande,
    VentesFacture, Paiement, Panier, ItemPanier,
    AvisClient, CodePromo
)


@admin.register(VentesSticker)
class VentesStickerAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'type_sticker', 'prix_ht', 'prix_ttc', 
                   'quantite', 'stock_minimum', 'actif_display', 'categorie')
    list_filter = ('type_sticker', 'materiau', 'categorie', 'actif')
    search_fields = ('code', 'nom', 'description')
    readonly_fields = ('created_at', 'updated_at', 'date_derniere_vente')
    fieldsets = (
        ('Informations produit', {
            'fields': ('code', 'nom', 'description', 'type_sticker', 'categorie', 'tags')
        }),
        ('Caractéristiques', {
            'fields': ('materiau', 'largeur_mm', 'hauteur_mm', 'forme', 'poids_g')
        }),
        ('Prix', {
            'fields': ('prix_ht', 'taux_tva')
        }),
        ('Stock', {
            'fields': ('quantite', 'stock_minimum', 'stock_securite')
        }),
        ('Personnalisation', {
            'fields': ('est_personnalisable', 'delai_personnalisation')
        }),
        ('Images', {
            'fields': ('image_principale', 'images_supplementaires')
        }),
        ('Métadonnées', {
            'fields': ('code_barres', 'actif', 'est_populaire', 'est_nouveau')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'date_derniere_vente')
        }),
    )
    
    def actif_display(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    actif_display.short_description = 'Statut'
    
    def prix_ttc(self, obj):
        return f"{obj.prix_ttc}€"
    prix_ttc.short_description = 'Prix TTC'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('code_client', 'nom_complet', 'email', 'type_client', 
                   'est_actif_display', 'nombre_commandes', 'montant_total_achats')
    list_filter = ('type_client', 'est_actif', 'ville')
    search_fields = ('code_client', 'email', 'prenom', 'nom', 'entreprise')
    readonly_fields = ('created_at', 'updated_at', 'date_premier_achat', 
                      'date_dernier_achat', 'montant_total_achats', 
                      'nombre_commandes', 'points_fidelite')
    
    def est_actif_display(self, obj):
        if obj.est_actif:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    est_actif_display.short_description = 'Statut'
    
    def nom_complet(self, obj):
        return obj.nom_complet
    nom_complet.short_description = 'Nom'


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'statut_display', 'date_creation', 
                   'montant_total_ttc', 'statut_paiement_display')
    list_filter = ('statut', 'statut_paiement', 'mode_livraison', 'date_creation')
    search_fields = ('numero', 'client__nom', 'client__prenom', 'client__email')
    readonly_fields = ('created_at', 'updated_at', 'date_confirmation',
                      'date_expedition', 'date_livraison', 'date_paiement')
    
    def statut_display(self, obj):
        colors = {
            'brouillon': 'gray',
            'en_attente': 'orange',
            'confirmee': 'blue',
            'preparation': 'purple',
            'expediee': 'green',
            'livree': 'darkgreen',
            'annulee': 'red',
        }
        color = colors.get(obj.statut, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_statut_display())
    statut_display.short_description = 'Statut'
    
    def statut_paiement_display(self, obj):
        colors = {
            'en_attente': 'orange',
            'partiel': 'blue',
            'paye': 'green',
            'retard': 'red',
            'annule': 'darkred',
        }
        color = colors.get(obj.statut_paiement, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_statut_paiement_display())
    statut_paiement_display.short_description = 'Paiement'


@admin.register(VentesFacture)
class VentesFactureAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'demande', 'date_emission', 
                   'montant_ttc', 'statut_display', 'est_retard_display')
    list_filter = ('statut', 'date_emission')
    search_fields = ('numero', 'client__nom', 'client__prenom', 'demande__numero')
    readonly_fields = ('created_at', 'updated_at', 'date_paiement')
    
    def statut_display(self, obj):
        colors = {
            'brouillon': 'gray',
            'emise': 'blue',
            'envoyee': 'orange',
            'payee': 'green',
            'annulee': 'red',
        }
        color = colors.get(obj.statut, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_statut_display())
    statut_display.short_description = 'Statut'
    
    def est_retard_display(self, obj):
        if obj.est_retard:
            return format_html('<span style="color: red;">⚠ En retard</span>')
        return ''
    est_retard_display.short_description = 'Retard'


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'client', 'facture', 'montant', 
                   'mode', 'date_paiement', 'est_valide_display')
    list_filter = ('mode', 'est_valide', 'date_paiement')
    search_fields = ('reference', 'client__nom', 'client__prenom', 'facture__numero')
    readonly_fields = ('created_by', 'updated_at', 'date_enregistrement')
    
    def est_valide_display(self, obj):
        if obj.est_valide:
            return format_html('<span style="color: green;">✓ Valide</span>')
        return format_html('<span style="color: red;">✗ Invalide</span>')
    est_valide_display.short_description = 'Validité'


@admin.register(AvisClient)
class AvisClientAdmin(admin.ModelAdmin):
    list_display = ('client', 'sticker', 'note_etoiles', 'titre', 
                   'est_valide_display', 'created_at')
    list_filter = ('note', 'est_valide', 'est_modere')
    search_fields = ('client__nom', 'client__prenom', 'sticker__nom', 'titre')
    readonly_fields = ('created_at', 'updated_at', 'utile_oui', 'utile_non')
    
    def note_etoiles(self, obj):
        return obj.note_etoiles
    note_etoiles.short_description = 'Note'
    
    def est_valide_display(self, obj):
        if obj.est_valide:
            return format_html('<span style="color: green;">✓ Validé</span>')
        return format_html('<span style="color: orange;">⏳ En attente</span>')
    est_valide_display.short_description = 'Validation'


@admin.register(CodePromo)
class CodePromoAdmin(admin.ModelAdmin):
    list_display = ('code', 'type_reduction', 'valeur', 'date_debut', 
                   'date_fin', 'utilisations_actuelles', 'est_actif_display')
    list_filter = ('type_reduction', 'est_actif')
    search_fields = ('code', 'description')
    
    def est_actif_display(self, obj):
        if obj.est_actif:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    est_actif_display.short_description = 'Statut'


# Enregistrement des autres modèles
admin.site.register(LigneDemande)
admin.site.register(Panier)
admin.site.register(ItemPanier)