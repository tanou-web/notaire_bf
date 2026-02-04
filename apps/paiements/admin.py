from django.contrib import admin
from django.utils.html import format_html
from .models import PaiementsTransaction


@admin.register(PaiementsTransaction)
class PaiementsTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reference', 'demande_link', 'type_paiement_display',
        'montant_formate', 'commission_formate', 'statut_display',
        'date_creation', 'date_validation'
    )
    list_filter = ('type_paiement', 'statut', 'date_creation')
    search_fields = ('reference', 'demande__reference')
    readonly_fields = ('date_creation', 'date_maj', 'date_validation')
    list_per_page = 20
    
    fieldsets = (
        ('Informations', {
            'fields': ('reference', 'demande', 'type_paiement', 'statut')
        }),
        ('Montants', {
            'fields': ('montant', 'commission')
        }),
        ('Données API', {
            'fields': ('donnees_api',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_maj', 'date_validation'),
            'classes': ('collapse',)
        }),
    )
    
    def demande_link(self, obj):
        if obj.demande:
            return format_html(
                '<a href="/admin/demandes/demandesdemande/{}/change/">{}</a>',
                obj.demande.id,
                obj.demande.reference
            )
        return "-"
    demande_link.short_description = 'Demande'
    
    def type_paiement_display(self, obj):
        return obj.get_type_paiement_display()
    type_paiement_display.short_description = 'Type'
    
    def statut_display(self, obj):
        colors = {
            'initie': 'gray',
            'en_attente': 'orange',
            'reussi': 'green',
            'validee': 'green',
            'echec': 'red',
            'echouee': 'red'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_display.short_description = 'Statut'
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FCFA".replace(",", " ")
    montant_formate.short_description = 'Montant'
    
    def commission_formate(self, obj):
        return f"{obj.commission:,.0f} FCFA".replace(",", " ")
    commission_formate.short_description = 'Commission'