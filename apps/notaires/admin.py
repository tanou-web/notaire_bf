# apps/notaires/admin.py - VERSION CORRIGÉE
from django.contrib import admin
from django.utils.html import format_html
from .models import NotairesNotaire, NotairesCotisation  # ✅ SEULEMENT ces 2

@admin.register(NotairesNotaire)
class NotaireAdmin(admin.ModelAdmin):
    list_display = (
        'matricule', 'nom_complet', 'email',
        'assurance_rc_status', 'assurance_rc_date_echeance',
        'actif_display'
    )


    list_filter = ('actif', 'region', 'ville')
    search_fields = ('matricule', 'nom', 'prenom', 'email', 'telephone')
    readonly_fields = ('created_at', 'updated_at', 'total_ventes', 'total_cotisations')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'nom', 'prenom', 'email', 'telephone', 'photo')
        }),
        ('Assurance Responsabilité Civile', {
            'fields': ('assurance_rc_date_echeance',)
        }), 
        ('Localisation', {
            'fields': ('region', 'ville', 'adresse')
        }),
        ('Statistiques', {
            'fields': ('total_ventes', 'total_cotisations')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    def assurance_rc_status(self, obj):
        if obj.assurance_rc_valide:
            return format_html('<span style="color: green;">✅ Valide</span>')
        return format_html('<span style="color: red;">❌ Expirée</span>')

    assurance_rc_status.short_description = "Assurance RC"

    
    def nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"
    nom_complet.short_description = 'Nom complet'
    
    def region_display(self, obj):
        if obj.region:
            return obj.region.nom
        return "-"
    region_display.short_description = 'Région'
    
    def ville_display(self, obj):
        if obj.ville:
            return obj.ville.nom
        return "-"
    ville_display.short_description = 'Ville'
    
    def actif_display(self, obj):
        if obj.actif:
            return format_html('<span style="color: green; font-weight: bold;">✅ Actif</span>')
        return format_html('<span style="color: red; font-weight: bold;">❌ Inactif</span>')
    actif_display.short_description = 'Statut'

@admin.register(NotairesCotisation)
class CotisationAdmin(admin.ModelAdmin):
    list_display = ('notaire_display', 'annee', 'montant_display', 
                   'statut_display', 'date_paiement')
    list_filter = ('statut', 'annee')
    search_fields = ('notaire__nom', 'notaire__prenom', 'notaire__matricule')
    
    def notaire_display(self, obj):
        return f"{obj.notaire.nom} {obj.notaire.prenom}"
    notaire_display.short_description = 'Notaire'
    
    def montant_display(self, obj):
        return f"{obj.montant} FCFA"
    montant_display.short_description = 'Montant'
    
    def statut_display(self, obj):
        if obj.statut == 'payee':
            return format_html('<span style="color: green; font-weight: bold;">✅ Payée</span>')
        return format_html('<span style="color: red; font-weight: bold;">❌ Impayée</span>')
    statut_display.short_description = 'Statut'