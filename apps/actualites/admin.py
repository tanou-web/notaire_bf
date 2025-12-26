from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ActualitesActualite


@admin.register(ActualitesActualite)
class ActualitesActualiteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'titre', 'categorie_display', 'auteur_nom',
        'date_publication', 'important', 'publie', 'vue',
        'featured', 'est_publiee', 'created_at', 'image_preview'
    )
    list_filter = (
        'categorie', 'important', 'publie', 'featured',
        'date_publication', 'created_at'
    )
    search_fields = ('titre', 'contenu', 'resume', 'slug', 'auteur__username')
    list_editable = ('important', 'publie', 'featured')
    readonly_fields = ('vue', 'slug', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('titre',)}
    raw_id_fields = ('auteur',)
    date_hierarchy = 'date_publication'
    list_per_page = 20
    actions = ['publier_actualites', 'depublier_actualites', 'marquer_comme_important']
    
    fieldsets = (
        ('Contenu', {
            'fields': ('titre', 'slug', 'contenu', 'resume', 'categorie')
        }),
        ('Médias', {
            'fields': ('image_principale',)
        }),
        ('Publication', {
            'fields': ('auteur', 'date_publication', 'important', 'publie', 'featured')
        }),
        ('Statistiques', {
            'fields': ('vue',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def categorie_display(self, obj):
        return obj.categorie_display
    categorie_display.short_description = 'Catégorie'
    
    def auteur_nom(self, obj):
        if obj.auteur:
            return f"{obj.auteur.nom} {obj.auteur.prenom}" if hasattr(obj.auteur, 'nom') else obj.auteur.username
        return "Anonyme"
    auteur_nom.short_description = 'Auteur'
    
    def est_publiee(self, obj):
        return obj.est_publiee
    est_publiee.boolean = True
    est_publiee.short_description = 'Publiée?'
    
    def image_preview(self, obj):
        if obj.image_principale:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image_principale)
        return "-"
    image_preview.short_description = 'Image'
    
    # Actions personnalisées
    def publier_actualites(self, request, queryset):
        """Publier les actualités sélectionnées"""
        updated = queryset.update(publie=True, date_publication=timezone.now())
        self.message_user(request, f"{updated} actualité(s) publiée(s).")
    publier_actualites.short_description = "Publier les actualités sélectionnées"
    
    def depublier_actualites(self, request, queryset):
        """Dépublier les actualités sélectionnées"""
        updated = queryset.update(publie=False)
        self.message_user(request, f"{updated} actualité(s) dépubliée(s).")
    depublier_actualites.short_description = "Dépublier les actualités sélectionnées"
    
    def marquer_comme_important(self, request, queryset):
        """Marquer comme important"""
        updated = queryset.update(important=True)
        self.message_user(request, f"{updated} actualité(s) marquée(s) comme importante(s).")
    marquer_comme_important.short_description = "Marquer comme important"
    
    # Méthodes pour personnaliser l'affichage dans le formulaire
    def get_readonly_fields(self, request, obj=None):
        """Rendre certains champs en lecture seule selon le contexte"""
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj and obj.publie:
            # Une fois publié, on ne peut plus changer certains champs
            return readonly_fields + ('date_publication',)
        return readonly_fields
    
    # Personnalisation de l'affichage de la liste
    def get_list_display(self, request):
        """Adapter l'affichage selon les permissions"""
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            # Cacher certaines colonnes pour les non-superusers
            return [field for field in list_display if field not in ['featured']]
        return list_display