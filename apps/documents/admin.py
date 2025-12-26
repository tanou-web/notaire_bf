from django.contrib import admin
from .models import DocumentsDocument, DocumentsTextelegal
from django.utils.html import format_html

@admin.register(DocumentsDocument)
class DocumentsDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference', 'nom', 'prix_formate','delai_affichage', 'actif', 'created_at', 'updated_at')
    list_filter = ('actif', 'delai_heures', 'created_at', 'updated_at')
    search_fields = ('reference', 'nom', 'description')
    list_editable = ('actif',)
    ordering = ('nom', 'reference')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informations de base', {
            'fields': ('reference', 'nom', 'description')
        }),
        ('Tarification et délai', {
            'fields': ('prix', 'delai_heures')
        }),
        ('Dates',{
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def prix_formate(self, obj):
        return f"{obj.prix:,.0f} FCFA".replace(',', ' ')
    prix_formate.short_description = 'Prix (FCFA)'

    def delai_affichage(self, obj):
        return obj.get_delai_display()
    delai_affichage.short_description = 'Délai'

@admin.register(DocumentsTextelegal)
class DocumentsTextelegalAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_texte_display', 'reference', 'titre', 'fichier_lien', 'date_publication', 'ordre', 'created_at')
    list_filter = ('type_texte', 'date_publication', 'created_at')
    search_fields = ('reference', 'titre', 'type_texte')
    ordering = ('type_texte', 'ordre', 'titre')
    
    fieldsets = (
        ('Informations', {
            'fields': ('type_texte', 'reference', 'titre', 'fichier', 'date_publication', 'ordre')
        }),
        ('Fichier et date', {
            'fields': ('fichier', 'date_publication'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Ordre d\'affichage', {
            'fields': ('ordre',),
        }),
    )

    def type_texte_display(self, obj):
        return obj.get_type_texte_display()
    type_texte_display.short_description = 'Type de Texte'

    def fichier_lien(self, obj):
        if obj.fichier:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.fichier)
        return "Aucun fichier"
    fichier_lien.short_description = 'Fichier'