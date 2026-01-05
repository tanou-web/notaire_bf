from django.contrib import admin
from .models import DemandesDemande, DemandesPieceJointe

@admin.register(DemandesDemande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('reference', 'statut', 'created_at')
    list_filter = ('statut', 'created_at')
    search_fields = ('reference', 'email_reception')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DemandesPieceJointe)
class PieceJointeAdmin(admin.ModelAdmin):
    list_display = ('demande', 'type_piece', 'nom_original', 'taille_formatee', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'nom_original', 'taille_fichier')
    fieldsets = (
        ('Informations', {'fields': ('demande', 'type_piece', 'fichier', 'description')}),
        ('Détails', {'fields': ('nom_original', 'taille_fichier', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
