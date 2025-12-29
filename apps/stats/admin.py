from django.contrib import admin
from django.utils.html import format_html
from .models import StatsVisite, PageVue, Referent, PaysVisite, PeriodeActive

@admin.register(StatsVisite)
class StatsVisiteAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'visites', 'pages_vues', 'pages_par_visite', 
        'taux_rebond', 'duree_moyenne', 'est_weekend_column'
    )
    list_filter = ('date',)  # pas 'est_weekend' car c'est une propriété
    search_fields = ('date',)
    date_hierarchy = 'date'
    ordering = ('-date',)
    readonly_fields = (
        'pages_par_visite', 'duree_totale', 'trafic_total', 
        'jour_semaine', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('date', 'visites', 'pages_vues', 'visites_authentifiees')
        }),
        ('Métriques avancées', {
            'fields': ('duree_moyenne', 'taux_rebond')
        }),
        ('Sources de trafic', {
            'fields': ('trafic_direct', 'trafic_reference', 'trafic_recherche', 'trafic_social')
        }),
        ('Calculs automatiques', {
            'fields': ('pages_par_visite', 'duree_totale', 'trafic_total', 'jour_semaine')
        }),
    )

    def est_weekend_column(self, obj):
        """Affiche un symbole coloré selon le type de jour."""
        if obj.est_weekend:
            return format_html('<span style="color: green;">✓ Weekend</span>')
        return format_html('<span style="color: blue;">Semaine</span>')
    est_weekend_column.short_description = 'Type de jour'

@admin.register(PageVue)
class PageVueAdmin(admin.ModelAdmin):
    list_display = ('date', 'titre', 'url', 'vues', 'temps_moyen')
    list_filter = ('date',)
    search_fields = ('url', 'titre')

@admin.register(Referent)
class ReferentAdmin(admin.ModelAdmin):
    list_display = ('date', 'domaine', 'visites')
    list_filter = ('date', 'domaine')
    search_fields = ('domaine', 'url')

@admin.register(PaysVisite)
class PaysVisiteAdmin(admin.ModelAdmin):
    list_display = ('date', 'pays', 'code_pays', 'visites')
    list_filter = ('date', 'pays')
    search_fields = ('pays', 'code_pays')

@admin.register(PeriodeActive)
class PeriodeActiveAdmin(admin.ModelAdmin):
    list_display = ('date', 'heure', 'visites')
    list_filter = ('date', 'heure')
