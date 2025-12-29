from django.contrib import admin
from django.utils.html import format_html
from .models import OrganisationMembrebureau, OrganisationHistorique, OrganisationMission

@admin.register(OrganisationMembrebureau)
class MembreBureauAdmin(admin.ModelAdmin):
    """Admin pour les membres du bureau"""
    
    list_display = [
        'photo_preview', 'nom_complet', 'poste_display',
        'ordre', 'actif_badge', 'en_mandat_badge',
        'date_entree', 'telephone', 'actions_buttons'  # renommé pour éviter conflit
    ]
    
    list_filter = ['poste', 'actif', 'date_entree']
    search_fields = ['nom', 'prenom', 'poste', 'email', 'telephone']
    ordering = ['ordre', 'nom', 'prenom']
    
    fieldsets = (
        ('Informations Personnelles', {
            'fields': (
                'nom', 'prenom', 'poste', 'photo_preview', 'photo',
                'telephone', 'email', 'biographie'
            )
        }),
        ('Mandat et Statut', {
            'fields': (
                'ordre', 'actif', 'date_entree', 'date_sortie',
                'mandat_debut', 'mandat_fin'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['photo_preview', 'created_at', 'updated_at']
    
    actions = ['activer_selection', 'desactiver_selection']
    
    # Champs personnalisés
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width:100px;max-height:100px;border-radius:5px;" />',
                obj.photo.url
            )
        return format_html('<span style="color:#999;">Pas de photo</span>')
    photo_preview.short_description = 'Photo'
    
    def nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}"
    nom_complet.short_description = 'Nom complet'
    
    def poste_display(self, obj):
        return obj.get_poste_display()
    poste_display.short_description = 'Poste'
    
    def actif_badge(self, obj):
        color = '#4CAF50' if obj.actif else '#F44336'
        text = 'Actif' if obj.actif else 'Inactif'
        return format_html(
            '<span style="background-color:{};color:white;padding:2px 8px;border-radius:10px;">{}</span>',
            color, text
        )
    actif_badge.short_description = 'Statut'
    
    def en_mandat_badge(self, obj):
        if obj.est_en_mandat:
            return format_html(
                '<span style="background-color:#4CAF50;color:white;padding:2px 8px;border-radius:10px;">En mandat</span>'
            )
        return format_html(
            '<span style="background-color:#FF9800;color:white;padding:2px 8px;border-radius:10px;">Hors mandat</span>'
        )
    en_mandat_badge.short_description = 'Mandat'
    
    def actions_buttons(self, obj):  # anciennement actions
        view_url = f'/admin/organisation/organisationmembrebureau/{obj.id}/change/'
        return format_html(
            '<a href="{}" class="button" style="background-color:#2196F3;color:white;padding:5px 10px;border-radius:3px;">Voir</a>',
            view_url
        )
    actions_buttons.short_description = 'Actions'
    
    # Actions personnalisées
    def activer_selection(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, f"{queryset.count()} membre(s) activé(s)")
    activer_selection.short_description = "Activer les membres sélectionnés"
    
    def desactiver_selection(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, f"{queryset.count()} membre(s) désactivé(s)")
    desactiver_selection.short_description = "Désactiver les membres sélectionnés"


# ========================================
# Historique et Missions restent inchangés
# ========================================

@admin.register(OrganisationHistorique)
class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ['titre', 'date_evenement', 'ordre', 'actif', 'created_at']
    list_filter = ['actif', 'date_evenement']
    search_fields = ['titre', 'contenu']
    ordering = ['ordre', 'date_evenement']
    fieldsets = (
        ('Contenu', {'fields': ('titre', 'contenu', 'date_evenement', 'image')}),
        ('Affichage', {'fields': ('ordre', 'actif')}),
    )


@admin.register(OrganisationMission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ['titre', 'icone', 'ordre', 'actif', 'created_at']
    list_filter = ['actif']
    search_fields = ['titre', 'description']
    ordering = ['ordre', 'titre']
    fieldsets = (
        ('Contenu', {'fields': ('titre', 'description', 'icone')}),
        ('Affichage', {'fields': ('ordre', 'actif')}),
    )
