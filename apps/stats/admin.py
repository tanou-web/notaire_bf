# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import StatsVisite, PageVue, Referent, PaysVisite, PeriodeActive

@admin.register(StatsVisite)
class StatsVisiteAdmin(admin.ModelAdmin):
    list_display = ('date', 'visites', 'pages_vues', 'pages_par_visite_column', 
                    'taux_rebond', 'duree_moyenne', 'est_weekend_column')
    list_filter = ('date', 'est_weekend')
    search_fields = ('date',)
    date_hierarchy = 'date'
    ordering = ('-date',)
    readonly_fields = ('pages_par_visite', 'duree_totale', 'trafic_total', 'jour_semaine')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('date', 'visites', 'pages_vues', 'visites_authentifiees')
        }),
        ('Métriques avancées', {
            'fields': ('duree_moyenne', 'taux_rebond')
        }),
        ('Sources de trafic', {
            'fields': ('trafic_direct', 'trafic_reference', 
                      'trafic_recherche', 'trafic_social')
        }),
        ('Calculs automatiques', {
            'fields': ('pages_par_visite', 'duree_totale', 
                      'trafic_total', 'jour_semaine')
        }),
    )
    
    def pages_par_visite_column(self, obj):
        return f"{obj.pages_par_visite:.2f}"
    pages_par_visite_column.short_description = 'Pages/visite'
    
    def est_weekend_column(self, obj):
        if obj.est_weekend:
            return format_html('<span style="color: green;">✓ Weekend</span>')
        return format_html('<span style="color: blue;">Semaine</span>')
    est_weekend_column.short_description = 'Type de jour'
    
    def changelist_view(self, request, extra_context=None):
        # Ajouter des statistiques agrégées à la vue liste
        response = super().changelist_view(request, extra_context)
        
        if hasattr(response, 'context_data'):
            queryset = response.context_data['cl'].queryset
            total_visites = sum(obj.visites for obj in queryset)
            total_pages = sum(obj.pages_vues for obj in queryset)
            
            response.context_data['stats_agregees'] = {
                'total_visites': total_visites,
                'total_pages': total_pages,
                'moyenne_pages': round(total_pages / max(total_visites, 1), 2),
            }
        
        return response

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